/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.monitor;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import _int.nato.ncia.natxmlib.NATIMReader;
import _int.nato.ncia.natxmlib.NATOMReader;
import _int.nato.ncia.natxmlib.messages.NATxM;
import java.io.IOException;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.function.Consumer;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class MessageMonitor {
    protected final Consumer<ReceivedMessage> cons;
    protected final LinkedBlockingQueue<JTIDSDataFrame> bims=new LinkedBlockingQueue<>(16);
    protected final LinkedBlockingQueue<JTIDSDataFrame> boms=new LinkedBlockingQueue<>(16);
    
    public MessageMonitor(Consumer<ReceivedMessage> cons) {
        this.cons = cons;
    }
    public void pushBIM(JTIDSDataFrame frame) throws Exception {
        bims.put(frame);
    }
    public void pushBOM(JTIDSDataFrame frame) throws Exception {
        boms.put(frame);
    }
    protected TOMThread tomThread;
    protected TIMThread timThread;
    
    public void start() {
        tomThread = new TOMThread();
        tomThread.setUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() {
            @Override
            public void uncaughtException(Thread t, Throwable e) {
                System.out.println(e);
            }
        });
        timThread = new TIMThread();
        timThread.setUncaughtExceptionHandler(new Thread.UncaughtExceptionHandler() {
            @Override
            public void uncaughtException(Thread t, Throwable e) {
                System.out.println(e);
            }
        });
        timThread.start();
        tomThread.start();
    }
    public void stop() {
        timThread.interrupt();
        tomThread.interrupt();
    }
    protected final static JTIDSDataFrame END_FRAME = new JTIDSDataFrame() {
        @Override
        public int getWord(int idx) {
            throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
        }

        @Override
        public void setWord(int idx, int wvalue) {
            throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
        }

        @Override
        public byte[] getBytes() {
            throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
        }
    };
    
    public void onEndOfData() {
        try {
            bims.put(END_FRAME);
            boms.put(END_FRAME);
        } catch (InterruptedException ex) {
            Logger.getLogger(MessageMonitor.class.getName()).log(Level.SEVERE, null, ex);
        }
        try {
            tomThread.join();
            timThread.join();
        } catch (InterruptedException ex) {
            Logger.getLogger(MessageMonitor.class.getName()).log(Level.SEVERE, null, ex);
        }
    }
    public synchronized void onMessage(ReceivedMessage rm) {
        cons.accept(rm);
    }
    public class TOMThread extends Thread {
        public boolean finished=false;
        
        @Override
        public void run() {
            NATOMReader tomReader = new SpecialTOMReader(new MonitorFrameSource(boms),new Consumer<ReceivedMessage>() {
                @Override
                public void accept(ReceivedMessage t) {
                    if(t==null) {
                        finished=true;
                    }else {
                        onMessage(t);
                    }
                }
            });
            while(!finished) {
                try {
                    NATxM tom = tomReader.read();
                    if(tom==null) {
                        finished=true;
                    }
                } catch (IOException ex) {
                    break;
                }
            }            
        }        
    }
    public class TIMThread extends Thread {
        public boolean finished=false;
        
        @Override
        public void run() {
            NATIMReader timReader = new SpecialTIMReader(new MonitorFrameSource(bims),new Consumer<ReceivedMessage>() {
                @Override
                public void accept(ReceivedMessage t) {
                    if(t==null) {
                        finished=true;
                    }else {
                        onMessage(t);
                    }
                }
            });
            while(!finished) {
                try {
                    NATxM tim = timReader.read();
                    if(tim==null) {
                        finished=true;
                    }
                } catch (IOException ex) {
                    break;
                }
            }
        }        
    }
    public class MonitorFrameSource implements JTIDSDataFrameSource {
        protected final LinkedBlockingQueue<JTIDSDataFrame> queue;

        public MonitorFrameSource(LinkedBlockingQueue<JTIDSDataFrame> queue) {
            this.queue = queue;
        }
        
        @Override
        public JTIDSDataFrame read() throws IOException {
            try {
                JTIDSDataFrame frame = queue.take();
                if(frame==END_FRAME) {
                    return null;
                }else{
                    return frame;
                }
            } catch (InterruptedException ex) {
                throw new IOException(ex);
            }
        }

        @Override
        public void close() {
        }
    
    }
}
