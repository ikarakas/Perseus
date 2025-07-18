/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.DumpFile;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSink;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import _int.nato.ncia.natxmlib.NATOMReader;
import _int.nato.ncia.natxmlib.clock.OffsetClock;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.messages.NATIM_WRAP_AROUND;
import _int.nato.ncia.natxmlib.messages.NATOM_WRAP_AROUND;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01.DataBlock;
import _int.nato.ncia.natxmlib.messages.tom4.NATOM04;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM04;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM4_RequestRepyRecord_Request;
import _int.nato.ncia.natxmlib.messages.tom1.NATOM01;
import _int.nato.ncia.natxmlib.messages.tom4.MessageStatusRecord;
import _int.nato.ncia.natxmlib.types.Field;

import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.LinkedList;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class JTIDSHostEmulator {

    protected final JTIDSDataFrameSource bomSource;
    protected final JTIDSDataFrameSink bimSink;

    protected Thread receiveThread = null;
    protected Thread periodicThread = null;

    protected OffsetClock hostClock = new OffsetClock(SystemClock.getInstance(), Duration.ofSeconds(120));
    
    protected JTIDSInitData initData = new JTIDSInitData();

    public JTIDSHostEmulator(JTIDSDataFrameSource bomSource, JTIDSDataFrameSink bimSink) {
        this.bomSource = bomSource;
        this.bimSink = bimSink;
    }
    
    public void start() throws IOException {
        receiveThread=new Thread(BIMReaderRunnable);
        periodicThread=new Thread(PeriodicRunnable);
        initData.data.read("host_default.jdf");
        receiveThread.start();
        periodicThread.start();
    }
    protected final Object writeSyncObject = new Object();

    protected void writeFrame(JTIDSDataFrame frame) throws IOException {
        synchronized (writeSyncObject) {
            bimSink.write(frame);
        }
    }
    
    protected void writeTIM(NATxM tim) throws IOException {
        synchronized (writeSyncObject) {
            JTIDSDataFrame[] frames = tim.encode();
            for (JTIDSDataFrame frame : frames) {
                writeFrame(frame);
            }
        }
    }
    
    public void transmitWrapAround() throws IOException {
        writeTIM(new NATIM_WRAP_AROUND());
    }
    
    public void transmitTIM04() throws IOException {
        NATIM04 tim=NATIM04.create();
        tim.getField("TIME").setValue(TimeStamp.fromInstant(hostClock.now()));
        tim.getField("REQUEST_REPLY_1").setValue(new NATIM4_RequestRepyRecord_Request(NATIM4_RequestRepyRecord_Request.RequestType.STATUS_REQUEST, 2, 2, 30));
        tim.getField("REQUEST_REPLY_2").setValue(new NATIM4_RequestRepyRecord_Request(NATIM4_RequestRepyRecord_Request.RequestType.STATUS_REQUEST, 19, 13, 7));
        tim.getField("REQUEST_REPLY_3").setValue(new NATIM4_RequestRepyRecord_Request(NATIM4_RequestRepyRecord_Request.RequestType.STATUS_REQUEST, 8, 13, 1));
        writeTIM(tim);
    }
   
    protected NATOM04 lastTOM04 = null;

    protected void onTOM04(NATOM04 tom) {
        Instant now = SystemClock.getInstance().now();
        String ssstr = ((NATOM04) tom).getField("SYNC STATUS").getValue().toString();
//            System.out.println(SystemClock.getInstance().now()+":JHE:TERMINAL SYNC STATUS="+((NATOM04)tom).getField("SYNC STATUS").getValue().toString());
        for (int i = 1; i <= 6; i++) {
            Field<MessageStatusRecord> f = (Field<MessageStatusRecord>) (((NATOM04) tom).getField("STATUS_" + i));
            MessageStatusRecord msr = f.getValue();
            if (msr.getLoopbackId() == 0) {
                continue;
            }
//                System.out.println(SystemClock.getInstance().now()+":JHE:MESSAGE STATUS: loopbackId="+msr.getLoopbackId()+", status="+msr.getMessageStatus().toString());                
            int y = 10;
        }
        if (((Field<Boolean>) (((NATOM04) tom).getField("USER REFRESH"))).getValue()) {
            controller.doDownloadInitData();
        }
        if (((Field<Boolean>) (((NATOM04) tom).getField("INITIALIZATION FROM AOCP"))).getValue()) {
            controller.doTransferInitData();
        }
        lastTOM04 = (NATOM04) tom;
        lastTOM04ReceiveTime = now;
    }
    protected void onTOM01(NATOM01 tom01) {
        for(NATOM01.DataBlock db : tom01.getDatablocks()) {
            if(db.isInitData()) {
                System.out.println(SystemClock.getInstance().now() + ":JHE:INIT_DATA_REPORT:blkId="+db.getBlockId()+", wrdId="+db.getStartingDataWord()+", cnt="+db.getDataWords().length);                 
            }else if(db.isStatusData()) {
                System.out.println(SystemClock.getInstance().now() + ":JHE:STATUS_DATA_REPORT:blkId="+db.getBlockId()+", wrdId="+db.getStartingDataWord()+", cnt="+db.getDataWords().length);                                 
            }
        }

    }
    protected void onTOM(NATxM tom) throws IOException {
        Instant now = SystemClock.getInstance().now();
        if (tom instanceof NATOM_WRAP_AROUND) {
            lastWAReceiveTime=now;
        }else if(tom instanceof NATOM04) {
            onTOM04((NATOM04)tom);
        }else if(tom instanceof NATOM01) {
            onTOM01((NATOM01)tom);
        }
    }
    protected Instant lastWATransmitTime = Instant.MIN;
    protected Instant lastWAReceiveTime = Instant.MIN;
    
    protected Instant lastTIM04TransmitTime = Instant.MIN;
    protected Instant lastTOM04ReceiveTime = Instant.MIN;

    public final Runnable PeriodicRunnable = new Runnable() {

        protected void _run() throws IOException {
            Instant now = SystemClock.getInstance().now();
            if (Duration.between(lastWATransmitTime, now).compareTo(Duration.ofSeconds(10)) >= 0) {
                transmitWrapAround();
                lastWATransmitTime=now;
            }
            if (Duration.between(lastTIM04TransmitTime, now).compareTo(Duration.ofSeconds(1)) >= 0) {
                transmitTIM04();
                lastTIM04TransmitTime=now;
            }
        }

        @Override
        public void run() {
            while (!Thread.interrupted()) {
                try {
                    _run();
                    Thread.sleep(10);
                } catch (InterruptedException ex) {
                    break;
                } catch (Throwable t) {

                }
            }
        }
    };
    public final Runnable BIMReaderRunnable = new Runnable() {
        @Override
        public void run() {
            NATOMReader tr = new NATOMReader(bomSource);
            
            while(!Thread.interrupted()) {
                NATxM tom;
                try {
                    tom = tr.read();
                    if(tom==null) {
                        break;
                    }
                } catch (IOException ex) {
                    Logger.getLogger(JTIDSHostEmulator.class.getName()).log(Level.SEVERE, null, ex);
                    break;
                }
                try {
                    onTOM(tom);
                }catch(IOException ex) {
                    Logger.getLogger(JTIDSHostEmulator.class.getName()).log(Level.SEVERE, null, ex);
                    break;                    
                }                
            }
        }
    };
    protected boolean transmitInitDataChange(int blkId, int wrdId, int[] data) {
        LinkedList<DataBlock> dblist = new LinkedList<>();
        dblist.add(NATIM01.buildInitDataChange(blkId, wrdId, data));
        NATIM01 tim = NATIM01.create(dblist);
        try {
            writeTIM(tim);
            return true;
        } catch (IOException ex) {
            Logger.getLogger(JTIDSHostEmulator.class.getName()).log(Level.WARNING, null, ex);
            return false;
        }
    }
    protected Runnable l16txrunnable = new Runnable() {
        @Override
        public void run() {
            try {
                _run();
            } catch (IOException ex) {
                Logger.getLogger(JTIDSHostEmulator.class.getName()).log(Level.SEVERE, null, ex);
            }
        }

        public void _run() throws IOException {
            LinkedList<DumpFile.Record> bimList = new LinkedList<>();

            for (DumpFile.Record r : DumpFile.parse("../dumps/dump_20220708_115417")) {
                if (r.isTIM()) {
                    int timId= r.getCode(0, 1, 5);
                    if(timId==3) {
                        bimList.add(r);
                    }
                }
            }
            if(bimList.isEmpty()) {
                return;
            }
            Instant firstRecTime = bimList.getFirst().getTime();
            Instant startTime = Instant.now();
            
            for (DumpFile.Record rec : bimList) {
                Instant recTime = rec.getTime();
                Duration d = Duration.between(firstRecTime, recTime);
                Instant replayTime = startTime.plus(d);
                long sleepMillis = Duration.between(Instant.now(), replayTime).toMillis();
                if (sleepMillis > 0) {
                    try {
                        Thread.sleep(sleepMillis);
                    } catch (InterruptedException ex) {
                        break;
                    }
                }
                if(Thread.interrupted()) {
                    break;
                }
                writeFrame(rec);
            }
        }
    };
    protected Thread l16txthread = null;

    public class Controller {
        public void doNetEntryReset(boolean ntr, boolean etr) {
            if(etr) {
                initData.setWord(1, 5, initData.getWord(1,5)|0x0002);
            }else{
                initData.setWord(1, 5, initData.getWord(1,5)&~0x0002);                
            }
            if(ntr) {
                initData.setWord(1, 4, initData.getWord(1,4)|0x0010);
            }else{
                initData.setWord(1, 4, initData.getWord(1,4)&~0x0010);                
            }
            transmitInitDataChange(1, 4, new int[]{initData.getWord(1, 4),initData.getWord(1, 5)});
            transmitInitDataChange(63, 5, new int[]{0x0001});
        }
        public synchronized void doTransferL16(boolean active) {
            if(active) {
                if((l16txthread!=null) && l16txthread.isAlive()) {
                    return;
                }
                l16txthread=new Thread(l16txrunnable);
                l16txthread.start();
            }else{
                if(l16txthread==null) {
                    return;
                }
                if(!l16txthread.isAlive()) {
                    return;
                }
                l16txthread.interrupt();                
            }
        }
        public void doTransferInitData() {
            for(int i=1;i<=63;i++) {
                transmitInitDataChange(i, 2, initData.getWords(i, 2, 30));
            }
        }
        public void doDownloadInitData() {
            for(int i=1;i<=61;i+=3) {
                NATIM04 tim=NATIM04.create();
                tim.getField("TIME").setValue(TimeStamp.fromInstant(hostClock.now()));
                tim.getField("REQUEST_REPLY_1").setValue(new NATIM4_RequestRepyRecord_Request(NATIM4_RequestRepyRecord_Request.RequestType.INITIALIZATION_REQUEST, i, 2, 30));
                tim.getField("REQUEST_REPLY_2").setValue(new NATIM4_RequestRepyRecord_Request(NATIM4_RequestRepyRecord_Request.RequestType.INITIALIZATION_REQUEST, i+1, 2, 30));
                tim.getField("REQUEST_REPLY_3").setValue(new NATIM4_RequestRepyRecord_Request(NATIM4_RequestRepyRecord_Request.RequestType.INITIALIZATION_REQUEST, i+2, 2, 30));
                try {
                    writeTIM(tim);
                } catch (IOException ex) {
                    Logger.getLogger(JTIDSHostEmulator.class.getName()).log(Level.SEVERE, null, ex);
                }
            }
        }
        public void doRestartLoadCurrent() {
            transmitInitDataChange(0, 2, new int[]{0x2<<14});
        }
        public void doRestartLoadDefault() {
            transmitInitDataChange(0, 2, new int[]{0x3<<14});
        }
        public void doLoadComplete() {
            transmitInitDataChange(0, 2, new int[]{0x1<<14});
        }
        public String getTerminalTime() {
            if(lastTOM04==null)  {
                return null;
            }
            return lastTOM04.getField("TIME").getValue().toString();
        }
        public String getTerminalStatus() {
            Instant now = SystemClock.getInstance().now();
            if(Duration.between(lastTOM04ReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return "Terminal active";
            }
            if(Duration.between(lastWAReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return "Link active";
            }
            return "Inactive";
        }
        public String getSyncStatus() {
            Instant now = SystemClock.getInstance().now();
            if(Duration.between(lastTOM04ReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return lastTOM04.getField("SYNC STATUS").getValue().toString();
            }
            return "";
        }
        public boolean isInitDataRequired() {
            Instant now = SystemClock.getInstance().now();
            if(Duration.between(lastTOM04ReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return ((Field<Boolean>)(lastTOM04.getField("INITIALIZATION DATA REQUIRED"))).getValue();
            }
            return false;            
        }
        public boolean isInitDataConflict() {
            Instant now = SystemClock.getInstance().now();
            if(Duration.between(lastTOM04ReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return  ((Field<Boolean>)(lastTOM04.getField("INITIALIZATION DATA CONFLICT"))).getValue();
            }
            return false;            
        }
        public boolean isInitDataError() {
            Instant now = SystemClock.getInstance().now();
            if(Duration.between(lastTOM04ReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return  ((Field<Boolean>)(lastTOM04.getField("INITIALIZATION DATA ERROR"))).getValue();
            }
            return false;            
        }
        public boolean isInitializationComplete() {
            Instant now = SystemClock.getInstance().now();
            if(Duration.between(lastTOM04ReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return  ((Field<Boolean>)(lastTOM04.getField("INITIALIZATION COMPLETE"))).getValue();
            }
            return false;            
        }
        public boolean isTerminalFail() {
            Instant now = SystemClock.getInstance().now();
            if(Duration.between(lastTOM04ReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return  ((Field<Boolean>)(lastTOM04.getField("TERMINAL FAIL"))).getValue();
            }
            return false;            
        }
        public boolean isIPFFail() {
            Instant now = SystemClock.getInstance().now();
            if(Duration.between(lastTOM04ReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return  ((Field<Boolean>)(lastTOM04.getField("IPF FAIL"))).getValue();
            }
            return false;            
        }
        public boolean isSDUAlert() {
            Instant now = SystemClock.getInstance().now();
            if(Duration.between(lastTOM04ReceiveTime, now).compareTo(Duration.ofSeconds(15))<0) {
                return  ((Field<Boolean>)(lastTOM04.getField("SDU ALERT"))).getValue();
            }
            return false;            
        }
    }
    public final Controller controller = new Controller();
}
