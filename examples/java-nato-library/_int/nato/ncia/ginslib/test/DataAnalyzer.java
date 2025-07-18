/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib.test;

import _int.nato.ncia.ginslib.MessageType;
import _int.nato.ncia.ginslib.GINSDecoder;
import _int.nato.ncia.ginslib.GINSMessage;
import _int.nato.ncia.ginslib.raw.RawFile;
import _int.nato.ncia.ginslib.busmon.BusMonitorMessage;
import _int.nato.ncia.ginslib.busmon.CardMonFile;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.Consumer;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class DataAnalyzer {

    public static MessageType identify(BusMonitorMessage bm) {
        return MessageType.identify(bm.getRT(), bm.isTransmit(), bm.getSA(), bm.getLength());
    }

    public static void dump(int[] arr) {
        for (int i = 0; i < arr.length; i++) {
            System.out.print(String.format("0x%04x ", arr[i]));
        }

    }  

    //transmit means: RT shall transmit data
    //receive means: BC transfers data to RT

    public static RawFile.Record lastReplayRecord=null;
    public static Instant replayStartTime=null;
    public static long replayStartHardwareNanos;
    
    public static void processRecord_Replay(RawFile.Record rec) {
        Instant now = Instant.now();;
        if(replayStartTime==null) {
            replayStartTime=now;
            replayStartHardwareNanos=rec.getMicros()*1000L;            
        }
        long recordTimeDelta=rec.getMicros()*1000L-replayStartHardwareNanos;
        Instant replayTime=replayStartTime.plus(Duration.ofNanos(recordTimeDelta));
        Duration waitTime = Duration.between(now, replayTime);
        if(!waitTime.isNegative() && !waitTime.isZero()) {
            try {
                if(waitTime.compareTo(Duration.ofSeconds(1))>0) {
                    System.out.println("waiting:"+waitTime);
                }
                long wt_sec=waitTime.toMillis();
                int wt_ns=(int)(waitTime.toNanos()%1000000);
                if((wt_ns<0) || (wt_ns>999999999)) {
                    int y=10;
                }
                Thread.sleep(wt_sec, wt_ns);
            } catch (InterruptedException ex) {
                Logger.getLogger(DataAnalyzer.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
        processRecord(rec);
        
    }
    public static void process(BusMonitorMessage bm) {
        long micros = bm.getHardwareTimeStamp();
        MessageType mt = MessageType.identify(bm.getRT(), bm.isTransmit(), bm.getSA(), bm.getLength());

        GINSMessage gm = GINSDecoder.decode(mt, bm);
        if (gm == null) {
            return;
        }
        gm.setSource((bm.isTransmit()?10000:0)+bm.getRT()*100+bm.getSA());
        gm.setHardwareTime(Duration.ofNanos(micros * 1000));
        gm.setSystemReceiveTime(bm.getHostTime());
        gp.update(gm);        
    }
    public static TreeMap<String, Long> addrs = new TreeMap<>();
    public static void processRecord(RawFile.Record rec) {
        String str = rec.toString();
        //System.out.println(t.toString());
        //String str=(t.cwd_1_t?"T":"R")+":"+t.cwd_1_rt+":"+t.cwd_1_sa+":"+t.dw.length;
        Long cnt = addrs.get(str);
        if (cnt != null) {
            addrs.put(str, cnt + 1);
        } else {
            addrs.put(str, 1L);
        }

        BusMonitorMessage bm = rec.toBusMonitorMessage(0);
        Instant ts=Instant.ofEpochSecond(0).plus(Duration.ofNanos(rec.getMicros()*1000));
        bm.setHostTimeStamp(ts.toEpochMilli());
        process(bm);        
    }
    protected static GINSProcessor gp = new GINSProcessor();
    public static void main(String[] args) {
        try {
            main_cardmon(args);
        } catch (IOException ex) {
            Logger.getLogger(DataAnalyzer.class.getName()).log(Level.SEVERE, null, ex);
        }
        gp.finish();
    }
    public static void main_raw(String[] args) throws IOException {
        SystemClock.getInstance().setReplayMode();
        //final Instant startTime=Instant.ofEpochMilli((System.currentTimeMillis() / 86_400_000) * 86_400_000);
        final Instant startTime=Instant.parse("2022-03-29T00:00:00Z");
        
        RawFile.parse("../ginsdata/Export1553.RAW", new Consumer<RawFile.Record>() {
            @Override
            public void accept(RawFile.Record t) {
                Instant fudgedMessageTime = startTime.plus(Duration.ofNanos(t.getMicros() * 1000));

                SystemClock.getInstance().setReplayTime(fudgedMessageTime);
                processRecord(t);
            }
        });
        for (Map.Entry<String, Long> e : addrs.entrySet()) {
            System.out.println(e.getKey() + " = " + e.getValue());
        }
    }
    public static void main_cardmon(String[] args) throws IOException {
        SystemClock.getInstance().setReplayMode();
//        CardMonFile.read(Path.of("../ginsdata/cardmon.20221209_105217.brf"), new Consumer<BusMonitorMessage>() {
        CardMonFile.read(Path.of("../ginsdata/cardmon.20221209_102105.brf"), new Consumer<BusMonitorMessage>() {
            @Override
            public void accept(BusMonitorMessage t) {
                Instant fudgedMessageTime = Instant.parse("2022-12-09T00:00:00Z").plus(t.getHardwareChronoTimeStamp());

                //SystemClock.getInstance().setReplayTime(t.getHostTime());
                SystemClock.getInstance().setReplayTime(fudgedMessageTime);
                process(t);
            }
        });        
        for (Map.Entry<String, Long> e : addrs.entrySet()) {
            System.out.println(e.getKey() + " = " + e.getValue());
        }
    }
    public static void main_replay(String[] args) throws IOException {
        Thread pulseThread = new Thread(new Runnable() {
            @Override
            public void run() {
/*                while(true) {
                    try {
                        System.out.println("###"+Instant.now()+";"+gp.waitForNextUTCSecond());
                    } catch (InterruptedException ex) {
                        Logger.getLogger(DataAnalyzer.class.getName()).log(Level.SEVERE, null, ex);
                    }
                }
*/
            }
        });
        
        //pulseThread.start();
        
        RawFile.parse("../ginsdata/Export1553.RAW", new Consumer<RawFile.Record>() {
            @Override
            public void accept(RawFile.Record t) {
                processRecord_Replay(t);
            }
        });
    }
}
