package _int.nato.ncia.natxmlib.nav;

import _int.nato.ncia.ginslib.GINSDecoder;
import _int.nato.ncia.ginslib.GINSMessage;
import _int.nato.ncia.ginslib.GINS_T09;
import _int.nato.ncia.ginslib.GINS_T20;
import _int.nato.ncia.ginslib.MessageType;
import _int.nato.ncia.ginslib.busmon.BusMonitorMessage;
import _int.nato.ncia.ginslib.busmon.BusMonitorSocket;
import _int.nato.ncia.ginslib.busmon.CardMonFile;
import _int.nato.ncia.ginslib.ntdlc.record.Recorder;
import _int.nato.ncia.ginslib.raw.RawFile;
import _int.nato.ncia.ginslib.test.DataAnalyzer;
import _int.nato.ncia.ginslib.test.GINSProcessor;
import _int.nato.ncia.natxmlib.Config;
import _int.nato.ncia.natxmlib.clock.SimpleClock;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import fxmlib.fxm.FIM;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.function.Consumer;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class NAVModule extends GINSProcessor {

    protected boolean replayMode = true;
    protected boolean useIPStackReplay=true;
    protected boolean ignoreUTC=false;
    
    protected Consumer<NAVMessage> consumer;

    public NAVModule(Consumer<NAVMessage> consumer) {
        this.consumer = consumer;
        ignoreUTC=Config.getInstance().isIgnoreUTC();
        replayMode=Config.getInstance().isUseGINSReplay();
    }

    @Override
    public Instant calculateUTC(Instant systemTime) {
        if(!ignoreUTC) {
            return super.calculateUTC(systemTime);
        }else{
            return systemTime;
        }        
    }

    @Override
    protected void updateGPSPosition(Instant systemTime, Instant utc, GINS_T09 t09) {
        if(!ignoreUTC) {
            super.updateGPSPosition(systemTime, utc, t09); 
        }else{
            super.updateGPSPosition(systemTime, systemTime, t09);             
        }
    }
    
    protected Thread pulseThread;
    protected Thread readThread;
    protected Thread receiveThread;
    protected CardmonThread cardmonThread;
    
    public void start() {
        /*
        pulseThread = new Thread(timePulseProducer);
        pulseThread.setPriority(Thread.MAX_PRIORITY);
        pulseThread.setName("PULSETHREAD");
        pulseThread.start();
        */
        
        receiveThread = new BusMessageReceiveThread();
        receiveThread.setPriority(Thread.MAX_PRIORITY);
        receiveThread.setName("BUSRXTHREAD");
        receiveThread.start();
        
        if (replayMode) {
            readThread = new FileReplayThread("../ginsdata/cardmon.20221209_102105.brf");
            readThread.setPriority(Thread.MAX_PRIORITY);
            readThread.setName("REPLAY");
            readThread.start();
        }else{
            if(Config.getInstance().isRunCardmon()) {
                cardmonThread=new CardmonThread();
                cardmonThread.start();
            }
        }
    }
    public void stop() {
        pulseThread.interrupt();
        readThread.interrupt();
    }

    @Override
    protected void onT20(GINS_T20 t20) {
        if(!ignoreUTC) {
            super.onT20(t20);
        } 
    }

    @Override
    protected void transmitFIM(Instant systemTime, Instant utcTime, FIM fim) {
       consumer.accept(new TransmitFIM(systemTime, fim));
    }
   
    protected Instant lastBusMessageTime = Instant.ofEpochMilli(0);
    public boolean isMilBusActive() {
        return Duration.between(lastBusMessageTime,SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(3))<0;
    }
    public boolean isGPSActive() {
        if(isMilBusActive()) {
            if(lastT09_GPS!=null) {
                return Duration.between(lastT09_GPS.getSystemReceiveTime(),SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(2))<0;
            }else{
                return false;
            }
        }else{
            return false;
        }
    }
    public boolean isUTCActive() {
        if(isMilBusActive()) {
            if(lastT09_UTC!=null) {
                return Duration.between(lastT09_UTC.getSystemReceiveTime(),SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(2))<0;
            }else{
                return false;
            }
        }else{
            return false;
        }
    }
    public boolean isNAVActive() {
        if(isMilBusActive()) {
            if(lastT27!=null) {
                return Duration.between(lastT27.getSystemReceiveTime(),SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(2))<0;
            }else{
                return false;
            }
        }else{
            return false;
        }
    }
    public boolean isMilBusOpen() {
        if(readThread!=null) {
            return readThread.isAlive();
        }
        if(cardmonThread!=null) {
            return cardmonThread.isRunning();
        }
        return true;
    }
    public boolean isMilBusFail() {
        if(cardmonThread!=null) {
            return cardmonThread.isNoCard();
        }else{
            return false;
        }
    }
    public void onBusMessage(BusMonitorMessage bm) {
        Recorder.record(bm);
        lastBusMessageTime=SystemClock.getInstance().now();
        
        MessageType mt = MessageType.identify(bm.getRT(), bm.isTransmit(), bm.getSA(), bm.getLength());

        GINSMessage gm = GINSDecoder.decode(mt, bm);
        if (gm == null) {
            return;
        }
        //Instant fudgedMessageTime = Instant.ofEpochMilli((System.currentTimeMillis() / 86_400_000) * 86_400_000).plus(Duration.ofNanos(dayMicros * 1000));
        gm.setSystemReceiveTime(SystemClock.getInstance().now());
        update(gm);
    }
    protected final Consumer<BusMonitorMessage> bmConsumer = new Consumer<BusMonitorMessage>() {
        @Override
        public void accept(BusMonitorMessage t) {
            try {
                onBusMessage(t);
            } catch (Throwable th) {
                System.out.println(th);
            }
        }
    };
    protected final Runnable timePulseProducer = new Runnable() {
        @Override
        public void run() {
            
        }
    };
    protected class BusMessageReceiveThread extends Thread {
        @Override
        public void run() {
            try {
                BusMonitorSocket socket = new BusMonitorSocket(1553);
                while(!Thread.interrupted()) {
                    onBusMessage(socket.receive());
                }
                }catch(IOException ex) {                    
                }
        }            
    }

    protected class FileReplayThread extends Thread {

        protected final String fileName;

        protected Instant replayStartTime = null;
        protected long replayStartHardwareNanos;

        protected DatagramSocket transmitSocket;
        protected InetAddress    dstIP;
        
        
        public FileReplayThread(String fileName) {
            this.fileName = fileName;
        }
        protected void submitBusMonitorMessage(BusMonitorMessage bm) {
            byte[] data=bm.toBytes();
            
            if(useIPStackReplay) {
                try {
                    transmitSocket.send(new DatagramPacket(data, 0, data.length, dstIP, 1553));
                } catch (IOException ex) {
                }
            }else{
                onBusMessage(bm);
            }            
        }
        public void processRecord_RAW_Replay(RawFile.Record rec) {
            Instant now = Instant.now();
            if (replayStartTime == null) {
                replayStartTime = now;
                replayStartHardwareNanos = rec.getMicros() * 1000L;
            }
            long recordTimeDelta = rec.getMicros() * 1000L - replayStartHardwareNanos;
            Instant replayTime = replayStartTime.plus(Duration.ofNanos(recordTimeDelta));
            Duration waitTime = Duration.between(now, replayTime);
            if (!waitTime.isNegative() && !waitTime.isZero()) {
                try {
                    if (waitTime.compareTo(Duration.ofSeconds(1)) > 0) {
                        System.out.println("waiting:" + waitTime);
                    }
                    long wt_sec = waitTime.toMillis();
                    int wt_ns = (int) (waitTime.toNanos() % 1000000);
                    if ((wt_ns < 0) || (wt_ns > 999999999)) {
                        int y = 10;
                    }
                    Thread.sleep(wt_sec, wt_ns);
                } catch (InterruptedException ex) {
                    Logger.getLogger(DataAnalyzer.class.getName()).log(Level.SEVERE, null, ex);
                }
            }
            BusMonitorMessage bm = rec.toBusMonitorMessage(System.currentTimeMillis());
            submitBusMonitorMessage(bm);
        }
        public void processRecord_BRF_Replay(BusMonitorMessage bm) {
            Instant now = Instant.now();
            if (replayStartTime == null) {
                replayStartTime = now;
                replayStartHardwareNanos = bm.getHardwareTimeStamp() * 1000L;
            }
            long recordTimeDelta =  bm.getHardwareTimeStamp() * 1000L - replayStartHardwareNanos;
            Instant replayTime = replayStartTime.plus(Duration.ofNanos(recordTimeDelta));
            Duration waitTime = Duration.between(now, replayTime);
            if (!waitTime.isNegative() && !waitTime.isZero()) {
                try {
                    if (waitTime.compareTo(Duration.ofSeconds(1)) > 0) {
                        System.out.println("waiting:" + waitTime);
                    }
                    long wt_sec = waitTime.toMillis();
                    int wt_ns = (int) (waitTime.toNanos() % 1000000);
                    
                    Thread.sleep(wt_sec, wt_ns);
                } catch (InterruptedException ex) {
                    Logger.getLogger(DataAnalyzer.class.getName()).log(Level.SEVERE, null, ex);
                }
            }            
            submitBusMonitorMessage(bm);
        }

        @Override
        public void run() {
            try {
                transmitSocket = new DatagramSocket();
                dstIP = InetAddress.getLocalHost();
                if (fileName.toLowerCase().endsWith("raw")) {
                    RawFile.parse(fileName, new Consumer<RawFile.Record>() {
                        @Override
                        public void accept(RawFile.Record t) {
                            processRecord_RAW_Replay(t);
                        }
                    });
                } else if (fileName.toLowerCase().endsWith("brf")) {
                    CardMonFile.read(Path.of(fileName), new Consumer<BusMonitorMessage>() {
                        @Override
                        public void accept(BusMonitorMessage bm) {
                            processRecord_BRF_Replay(bm);
                        }
                    });
                    
                }
            } catch (IOException ex) {
                
            }
        }
    }

    @Override
    public SimpleClock getUTCClock() {
        return NAVUTCCLOCK;
    }

    @Override
    public Duration getUTCOffset() {
            if(ignoreUTC) {
                return Duration.ofNanos(0);
            }else{
                return super.getUTCOffset();
            }
    }
    
    protected final SimpleClock NAVUTCCLOCK = new SimpleClock() {
        protected final SimpleClock systemClock=SystemClock.getInstance();
        
        @Override
        public Instant now() {
            if(ignoreUTC) {
                return systemClock.now();
            }else{
                return UTCCLOCK.now();
            }
        }

        @Override
        public boolean isRunning() {
            if(ignoreUTC) {
                return systemClock.isRunning();
            }else{
                return UTCCLOCK.isRunning();
            }
            
        }
    };    
    protected class CardmonThread extends Thread {
        private static String OS = System.getProperty("os.name").toLowerCase();

        protected final boolean isWindows;
        protected boolean running=false;
        protected boolean nocard=false;
        protected Integer port;
        
        public CardmonThread() {
            super("CARDMON");
            setPriority(MAX_PRIORITY);            
            isWindows=OS.contains("win");
        }

        public boolean isRunning() {
            return running;
        }

        public boolean isNoCard() {
            return nocard;
        }
        
        protected InputStream runCommand(String... cmd) throws IOException {
            ProcessBuilder pb = new ProcessBuilder(cmd);
            Process proc = pb.start();
            if (proc != null) {
                return proc.getInputStream();
            }else {
                throw new IOException("no process");
            }
        }
        protected Integer getCardNumber() {
            Integer card=null;
            try {
                InputStream ins = runCommand("btlist64.exe");
                BufferedReader br = new BufferedReader(new InputStreamReader(ins));
                while (true) {
                    String line = br.readLine();
                    if (line == null) {
                        break;
                    }
                    if(line.startsWith("CARD") && (card==null)) {
                        String s0=line.substring(0, line.indexOf(","));
                        String[] sarr=s0.split(":");
                        String cstr=sarr[1].trim();
                        try {
                            card=Integer.parseInt(cstr);
                        }catch(Throwable t) {
                            
                        }
                    }
                }                
            } catch (IOException ex) {
            }
            return card;
        }
        protected boolean _run() throws IOException {
            if (isWindows) {
                nocard=true;
                Integer card=getCardNumber();
                if(card!=null) {
                    System.out.println("Using MilBus card #"+card);
                }
                InputStream ins;                
                try {
                    if(card==null) {
                        ins = runCommand("cardmon64.exe","-txa");
                    }else{
                        ins = runCommand("cardmon64.exe","-ca",""+card,"-txa");                        
                    }
                }catch(IOException ex) {
                    System.out.println("CARDMON64.EXE NOT FOUND");   
                    return false;
                }
                System.out.println("CARDMON STARTED");                        
                running = true;
                nocard=false;
                BufferedReader br = new BufferedReader(new InputStreamReader(ins));
                while (true) {
                    String line = br.readLine();
                    if (line == null) {
                        break;
                    }
                    if(line.contains("cant open card")) {
                        System.err.println("NO MILBUS CARD FOUND");                        
                        nocard=true;                        
                    }
                    if(line.startsWith("monitor_port")) {
                        try {
                            port = Integer.valueOf(line.split("=")[1].trim());
                        }catch(Throwable t) {                            
                        }
                    }
                }
                return !nocard;
            } else {
                nocard=true;
                InputStream ins = runCommand("ls", "-lsaR", "/home");
                running = true;
                nocard=false;
                BufferedReader br = new BufferedReader(new InputStreamReader(ins));
                while (true) {
                    String line = br.readLine();
                    if (line == null) {
                        break;
                    }
                    lastBusMessageTime=SystemClock.getInstance().now();
                }
                return true;
            }
        }
        @Override
        public void run() {
            while(!Thread.interrupted()) {
                try {
                    running=false;
                    nocard=true;
                    _run();
                    running=false;
                    nocard=true;
                }catch(Exception ex) {
                    System.out.println(ex);
                    running=false;
                }
                try {
                    Thread.sleep(5000);
                } catch (InterruptedException ex) {
                    break;
                }
            }
        }
        
    }
}
