package _int.nato.ncia.natxmlib.jic;

import _int.nato.ncia.natxmlib.Config;
import _int.nato.ncia.natxmlib.HICController;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSink;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class JICModule implements JTIDSDataFrameSink, JTIDSDataFrameSource {

    protected final static JICModule INSTANCE = new JICModule();

    public static JICModule getInstance() {
        return INSTANCE;
    }
    protected HICController jic = null;
    protected final Object syncObject = new Object();

    private JICModule() {
    }

    protected CreateThread createThread = new CreateThread();
    protected ReadThread readThread = new ReadThread();
    protected WriteThread writeThread = new WriteThread();
    protected String statusText = "";
    protected boolean active=false;
  
    public void start() {
        synchronized (syncObject) {
            if (!active) {
                createThread.start();
                writeThread.start();
                readThread.start();
                active = true;
            }
        }
    }

    public void stop() {
        synchronized (syncObject) {
            if (active) {
                createThread.interrupt();
                writeThread.interrupt();
                readThread.interrupt();
                active = false;
                readQueue.clear();
                writeQueue.clear();
            }
        }
    }
    @Override
    public void close() {
    }
    protected LinkedBlockingQueue<JTIDSDataFrame> readQueue = new LinkedBlockingQueue<>(8);

    @Override
    public JTIDSDataFrame read() throws IOException {
        try {
            return readQueue.take();
        } catch (InterruptedException ex) {
            throw new IOException(ex);
        }
    }
    protected LinkedBlockingQueue<WriteQueueEntry> writeQueue = new LinkedBlockingQueue<>(128);
    protected void onWritten(WriteQueueEntry wqe) {
        //System.out.println("#JIC_OUT:"+wqe.toString());
    }
    public boolean isJICConnected() {
        return jic!=null;
    }
    @Override
    public void write(JTIDSDataFrame frame) throws IOException {
        if (writeQueue.size() > 16) {

        }
        try {
            writeQueue.put(new WriteQueueEntry(frame));
        } catch (InterruptedException ex) {
            throw new IOException(ex);
        }
    }

    public class CreateThread extends Thread {

        public CreateThread() {
            super("JICConnectThread");
        }

        protected void serve() {
            while (!Thread.interrupted()) {
                synchronized (syncObject) {
                    if (jic == null) {
                        try {

                            jic = HICController.create(Config.getInstance().getJICPortName(), Config.getInstance().getJICBaudRate(), Config.getInstance().isJICFlowControl());
                            Logger.getLogger(JICModule.class.getName()).log(Level.INFO, "opened serial port {0}", Config.getInstance().getJICPortName());
                            jic.setRecording(Config.getInstance().isJICDumpEnabled(), Config.getInstance().getRecordingPath());
                            statusText = "active on " + Config.getInstance().getJICPortName();
                        } catch (Exception ex) {
                            Logger.getLogger(JICModule.class.getName()).log(Level.SEVERE, "failed to open serial port {0}", Config.getInstance().getJICPortName());
                            statusText = "failed to open serial port " + Config.getInstance().getJICPortName();
                        }
                    }
                }
                try {
                    Thread.sleep(5000);
                } catch (InterruptedException ex) {
                    break;
                }
            }
        }

        @Override
        public void run() {
            serve();
        }
    }

    public class ReadThread extends Thread {

        public ReadThread() {
            super("JICReadThread");
        }

        protected void serve() {
            while (!Thread.interrupted()) {
                HICController hc = null;
                synchronized (syncObject) {
                    hc = jic;
                }
                if (hc != null) {
                    try {
                        JTIDSDataFrame jdf = hc.read();
                        readQueue.put(jdf);
                    } catch (IOException ex) {
                        Logger.getLogger(JICModule.class.getName()).log(Level.SEVERE, "failed to read from serial port");
                        hc.close();
                        synchronized (syncObject) {
                            if (jic == hc) {
                                jic = null;
                            }
                        }
                    } catch (InterruptedException ex) {
                        break;
                    }
                } else {
                    try {
                        Thread.sleep(1000);
                    } catch (InterruptedException ex) {
                        break;
                    }
                }
            }
        }

        @Override
        public void run() {
            serve();
        }

    }

    public class WriteThread extends Thread {

        public WriteThread() {
            super("JICWriteThread");
        }

        protected void serve() {
            while (!Thread.interrupted()) {
                HICController hc;
                synchronized (syncObject) {
                    hc = jic;
                }
                if (hc != null) {
                    try {
                        WriteQueueEntry wqe=writeQueue.take();                        
                        JTIDSDataFrame jdf=wqe.frame;
                        wqe.taken();
                        hc.write(jdf);
                        wqe.written();
                        onWritten(wqe);
                    } catch (IOException ex) {
                        Logger.getLogger(JICModule.class.getName()).log(Level.SEVERE, "failed to write to serial port");
                        hc.close();
                        synchronized (syncObject) {
                            if (jic == hc) {
                                jic = null;
                            }
                        }
                    } catch (InterruptedException ex) {
                        break;
                    }
                } else {
                    try {
                        Thread.sleep(1000);
                    } catch (InterruptedException ex) {
                        break;
                    }
                }
            }
        }

        @Override
        public void run() {
            serve();
        }
    }
    protected class WriteQueueEntry {
        protected final JTIDSDataFrame frame;
        protected final long nanos;
        protected final int qsize;
        protected long takenNanos;
        protected long writtenNanos;

        public WriteQueueEntry(JTIDSDataFrame frame) {
            this.frame = frame;
            this.qsize=writeQueue.size();
            this.nanos=System.nanoTime();
        }
        protected void taken() {
            this.takenNanos=System.nanoTime();
        }
        protected void written() {
            this.writtenNanos=System.nanoTime();
        }
        public Duration getTime() {
            return Duration.ofNanos(writtenNanos-nanos);
        }

        @Override
        public String toString() {
            return "WriteQueueEntry{" + "qsize=" + qsize + ", time="+getTime()+'}';
        }
        
    }
}
