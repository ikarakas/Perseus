/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.ginslib.ntdlc.record.Recorder;
import _int.nato.ncia.natxmlib.Config;
import _int.nato.ncia.natxmlib.rarp.Jrarpd;
import _int.nato.ncia.natxmlib.test.MIDSModule.MTEngine;
import fxmlib.data.mids.transport.TerminalConnection;
import fxmlib.data.mids.transport.TerminalPlatformRConnection;
import fxmlib.data.mids.words.InitWord1865;
import fxmlib.data.mids.words.InitWord1866;
import fxmlib.data.mids.words.InitWord1867;
import fxmlib.data.mids.words.InitWord1880;
import fxmlib.data.mids.words.InitWord1881;
import fxmlib.fxm.FIM;
import fxmlib.fxm.FIM03_InitDataChange;
import fxmlib.fxm.FIM55;
import fxmlib.fxm.FIM56;
import fxmlib.fxm.FOM;
import fxmlib.fxm.FOMEvent;
import fxmlib.mids.BasicEngine;
import fxmlib.mids.EngineState;
import java.io.IOException;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Arrays;
import java.util.Collection;
import java.util.LinkedList;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class MIDSModule {

    protected String host;
    protected int port;

    protected MTEngine engine = null;
    protected final Connector connector = new Connector();
    protected final Thread connectorThread = new Thread(connector);
    protected final Object syncObject = new Object();
    protected Consumer<FOM> fomConsumer = null;
    protected Thread rarpdThread=new RarpThread();
    
    public MIDSModule(Consumer<FOM> fomConsumer) {
        this.host = Config.getInstance().getMidsIP();
        this.port = Config.getInstance().getMidsPort();
        this.fomConsumer = fomConsumer;
    }

    protected void init() {

    }

    protected void writeFIM(FIM fim) throws IOException {
        synchronized (syncObject) {
            if (engine != null) {
                engine.writeBIM(new FIM[]{fim});
                Recorder.record(fim);
                //               System.out.println(SystemClock.getInstance().now()+":JMG:writeFIM:"+fim.toString());
            }
        }
    }

    public EngineState getEngineState() {
        if (engine != null) {
            return engine.getState();
        } else {
            if (midsConnectionFailed) {
                return EngineState.FAILED_CONNECTING;
            } else {
                return EngineState.CONNECTING;
            }
        }
    }

    protected synchronized void writeBIM(Collection<FIM> bim) throws IOException {
        if (bim.isEmpty()) {
            return;
        }
        synchronized (syncObject) {
            if (engine != null) {
                engine.writeBIM(bim.toArray(new FIM[0]));
            }
            for (FIM fim : bim) {
                Recorder.record(fim);
            }
        }
    }

    public void start() {
        connectorThread.start();
        rarpdThread.start();
    }

    public void stop() {
        connectorThread.interrupt();
        rarpdThread.interrupt();
        
        if (engine != null) {
            engine.stop();
        }
    }

    public void setDateTime(Instant dt) throws IOException {
        ZonedDateTime zdt = ZonedDateTime.ofInstant(dt, ZoneId.of("UTC"));
        LinkedList<FIM> fimList = new LinkedList<>();

        InitWord1881 iw1881 = new InitWord1881(zdt.getYear() % 100);
        InitWord1880 iw1880 = new InitWord1880(zdt.getDayOfYear());
        InitWord1865 iw1865 = new InitWord1865(true, zdt.getHour(), zdt.getMinute());
        InitWord1866 iw1866 = new InitWord1866(zdt.getSecond());
        InitWord1867 iw1867 = new InitWord1867(true, 0, 12);
        FIM03_InitDataChange fim0 = new FIM03_InitDataChange(0, 1880, new int[]{iw1880.getCode(), iw1881.getCode()});
        FIM03_InitDataChange fim1 = new FIM03_InitDataChange(0, 1865, new int[]{iw1865.getCode(), iw1866.getCode(), iw1867.getCode()});
        fimList.add(fim0);
        fimList.add(fim1);

        writeBIM(fimList);
    }

    public boolean isOperational() {
        synchronized (syncObject) {
            if (engine == null) {
                return false;
            }
            return (engine.getState() == EngineState.RUNNING);
        }
    }

    protected class MTEngine extends BasicEngine {

        public MTEngine(TerminalConnection connection) {
            super(connection);
            super.setUserID(33);
        }

        @Override
        public void onFOM(FOMEvent fomEvent) {
            super.onFOM(fomEvent);
            //System.out.println("#FOM;" + Instant.now() + ";" + fomEvent.fom);
            MIDSModule.this.fomConsumer.accept(fomEvent.fom);
        }

        @Override
        protected void setNewState(EngineState newState) {
            super.setNewState(newState); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/OverriddenMethodBody
            if ((newState == EngineState.CLOSED) || (newState == EngineState.FAILED_CONNECTING) || (newState == EngineState.FAILED)) {
                midsConnectionFailed = true;
                stop();
            } else if (newState == EngineState.STOPPING) {
                synchronized (syncObject) {
                    MIDSModule.this.engine = null;
                }
            }

        }

        @Override
        protected FIM55.OptionalRecord[] getFIM55OptionalRecords() {
            LinkedList<FIM55.OptionalRecord> orlist = new LinkedList(Arrays.asList(super.getFIM55OptionalRecords()));
            orlist.add(new FIM55.OptionalRecord(1, true, false));
            orlist.add(new FIM55.OptionalRecord(2, true, false));
            orlist.add(new FIM55.OptionalRecord(4, true, false));
            orlist.add(new FIM55.OptionalRecord(12, true, false));
            orlist.add(new FIM55.OptionalRecord(17, true, false));
            orlist.add(new FIM55.OptionalRecord(20, true, false));
            orlist.add(new FIM55.OptionalRecord(1, false, false));
            orlist.add(new FIM55.OptionalRecord(2, false, false));
            orlist.add(new FIM55.OptionalRecord(3, false, false));
            orlist.add(new FIM55.OptionalRecord(4, false, false));
            orlist.add(new FIM55.OptionalRecord(30, false, false));
            orlist.add(new FIM55.OptionalRecord(31, false, false));
            return orlist.toArray(new FIM55.OptionalRecord[0]);
        }
        private static final FIM56.OptionalRecord[] defaultFIM56Records = {
            new FIM56.OptionalRecord(0, 0, 0, 1),
            new FIM56.OptionalRecord(0, 0, 0, 1),
            new FIM56.OptionalRecord(2, 0, 0, 0),
            new FIM56.OptionalRecord(2, 2, 0, 0),
            new FIM56.OptionalRecord(2, 3, 0, 0),
            new FIM56.OptionalRecord(2, 4, 0, 0),
            new FIM56.OptionalRecord(2, 5, 0, 0),
            new FIM56.OptionalRecord(2, 6, 0, 0),
            new FIM56.OptionalRecord(3, 0, 0, 0),
            new FIM56.OptionalRecord(3, 1, 0, 0),
            new FIM56.OptionalRecord(3, 2, 0, 0),
            new FIM56.OptionalRecord(3, 3, 0, 0),
            new FIM56.OptionalRecord(3, 4, 0, 0),
            new FIM56.OptionalRecord(3, 5, 0, 0),
            new FIM56.OptionalRecord(3, 6, 0, 0),
            new FIM56.OptionalRecord(3, 7, 0, 0),
            new FIM56.OptionalRecord(6, 0, 0, 0),
            new FIM56.OptionalRecord(7, 0, 0, 0),
            new FIM56.OptionalRecord(7, 1, 0, 0),
            new FIM56.OptionalRecord(7, 2, 0, 0),
            new FIM56.OptionalRecord(7, 3, 0, 0),
            new FIM56.OptionalRecord(7, 4, 0, 0),
            new FIM56.OptionalRecord(7, 5, 0, 0),
            new FIM56.OptionalRecord(7, 6, 0, 0),
            new FIM56.OptionalRecord(7, 7, 0, 0),
            new FIM56.OptionalRecord(8, 0, 0, 0),
            new FIM56.OptionalRecord(8, 1, 0, 0),
            new FIM56.OptionalRecord(9, 0, 0, 0),
            new FIM56.OptionalRecord(9, 1, 0, 0),
            new FIM56.OptionalRecord(10, 2, 0, 0),
            new FIM56.OptionalRecord(10, 3, 0, 0),
            new FIM56.OptionalRecord(10, 5, 0, 0),
            new FIM56.OptionalRecord(10, 6, 0, 0),
            new FIM56.OptionalRecord(12, 0, 0, 0),
            new FIM56.OptionalRecord(12, 1, 0, 0),
            new FIM56.OptionalRecord(12, 2, 0, 0),
            new FIM56.OptionalRecord(12, 3, 0, 0),
            new FIM56.OptionalRecord(12, 4, 0, 0),
            new FIM56.OptionalRecord(12, 5, 0, 0),
            new FIM56.OptionalRecord(12, 6, 0, 0),
            new FIM56.OptionalRecord(12, 7, 0, 0),
            new FIM56.OptionalRecord(13, 0, 0, 0),
            new FIM56.OptionalRecord(13, 2, 0, 0),
            new FIM56.OptionalRecord(13, 3, 0, 0),
            new FIM56.OptionalRecord(13, 4, 0, 0),
            new FIM56.OptionalRecord(13, 5, 0, 0),
            new FIM56.OptionalRecord(15, 0, 0, 0),
            new FIM56.OptionalRecord(16, 0, 0, 0),
            new FIM56.OptionalRecord(28, 2, 0, 0)
        };

        @Override
        protected FIM56.OptionalRecord[] getFIM56OptionalRecords() {
            return defaultFIM56Records;
        }
    }

    protected boolean midsConnectionFailed = true;

    protected class Connector implements Runnable {

        protected final Object waitObject = new Object();

        public void trigger() {
            synchronized (waitObject) {
                waitObject.notifyAll();
            }
        }

        @Override
        public void run() {
            while (!Thread.interrupted()) {
                boolean startUp = false;
                synchronized (syncObject) {
                    if (engine == null) {
                        startUp = true;
                    }
                }
                if (startUp) {
                    TerminalPlatformRConnection connection = new TerminalPlatformRConnection(host, port);
                    try {
                        connection.connect();
                        midsConnectionFailed = false;
                        MTEngine engine = new MTEngine(connection);
                        engine.start();
                        synchronized (syncObject) {
                            MIDSModule.this.engine = engine;
                        }
                    } catch (IOException ex) {
                        midsConnectionFailed = true;
                        Logger.getLogger(MIDSModule.class.getName()).log(Level.SEVERE, "MIDS connect to {0} on port {1} failed", new Object[]{host, port});
                    }
                }
                synchronized (waitObject) {
                    try {
                        waitObject.wait(5000);
                    } catch (InterruptedException ex) {
                        break;
                    }
                }
            }
        }
    }
    public class RarpThread extends Thread {
        public RarpThread() {
            setName("RARPD");
        }

        @Override
        public void run() {
            Jrarpd.strTargetIp=Config.getInstance().getMidsIP();
            
            while (!Thread.interrupted()) {
                try {
                    Jrarpd.SERVER.run();
                } catch (Throwable t) {
                }
                try {
                    TimeUnit.SECONDS.sleep(10);
                } catch (InterruptedException ex) {
                    Logger.getLogger(MIDSModule.class.getName()).log(Level.SEVERE, null, ex);
                }

            }
        }

    }
}
