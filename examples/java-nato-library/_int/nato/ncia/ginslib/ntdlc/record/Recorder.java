/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib.ntdlc.record;

import _int.nato.ncia.ginslib.busmon.BusMonitorMessage;
import static _int.nato.ncia.ginslib.ntdlc.record.Recorder.Type.BM;
import static _int.nato.ncia.ginslib.ntdlc.record.Recorder.Type.HIM;
import static _int.nato.ncia.ginslib.ntdlc.record.Recorder.Type.HOM;
import _int.nato.ncia.natxmlib.Config;
import _int.nato.ncia.natxmlib.HICController.HICFrame;
import _int.nato.ncia.natxmlib.HICDataFrame;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import static _int.nato.ncia.natxmlib.clock.SystemClock.UTC;
import fxmlib.fxm.FIM;
import fxmlib.fxm.FOM;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedList;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class Recorder {

    public static Recorder INSTANCE = new Recorder();
    protected final Path filePath;
    protected boolean available = false;
    protected boolean enabled = true;
    protected OutputStream outs;
    protected long writeSize = 0;
    protected final long MAX_FILESIZE = 64 * 1024 * 1024L;

    private Recorder(String filePathName, boolean enabled) {
        filePath = Path.of(filePathName);
        if (!Files.exists(filePath) && enabled) {
            try {
                Files.createDirectories(filePath);
                available = true;
            } catch (IOException ex) {
                Logger.getLogger(Recorder.class.getName()).log(Level.SEVERE, null, ex);
            }
        }else{
            available = enabled;            
        }
        this.enabled=enabled;
    }
    private Recorder() {
        this(Config.getInstance().getRecordingPath(), Config.getInstance().isRecordingEnabled());        
    }

    public static Recorder getInstance() {
        return INSTANCE;
    }

    protected final OutputStream nextFile() throws IOException {
        DateTimeFormatter tdf = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");
        Instant now = SystemClock.getInstance().now();
        String fileName = "ntdlc_rec_" + tdf.format(ZonedDateTime.ofInstant(now, UTC)) + ".rdf";
        Path recFilePath = filePath.resolve(fileName);
        if (Files.exists(recFilePath)) {
            throw new IOException("file " + recFilePath.toString() + " already exists");
        }
        return Files.newOutputStream(recFilePath, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
    }
    protected final Object syncObject = new Object();

    public void flush() throws IOException {
        synchronized (syncObject) {
            if (writeSize > 0) {
                outs.flush();
                outs.close();
                writeSize = 0L;
                outs = nextFile();
            }
        }

    }

    protected void write(byte[] data) throws IOException {
        synchronized (syncObject) {
            if(outs==null)  {
                outs = nextFile();    
            }
            if (writeSize + data.length > MAX_FILESIZE) {
                flush();
            }
            outs.write(data);
            writeSize += data.length;
        }
    }

    public void setEnabled(boolean enabled) {
        if (this.enabled && !enabled) {
            try {
                flush();
            } catch (IOException ex) {
                Logger.getLogger(Recorder.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
        this.enabled = enabled;
    }

    protected void write(Type type, byte[] data) throws IOException {
        Instant now = SystemClock.getInstance().now();
        ByteBuffer bb = ByteBuffer.allocate(Integer.SIZE + Long.SIZE + Integer.SIZE + Integer.SIZE + data.length);
        bb.putInt(type.ordinal());
        bb.putLong(now.getEpochSecond());
        bb.putInt(now.getNano());
        bb.putInt(data.length);
        bb.put(data);
        write(bb.array());
    }

    public static void record(Object obj) {
        if(INSTANCE.RecordThread.getState()==Thread.State.NEW) {
            INSTANCE.RecordThread.start();
        }
        synchronized (INSTANCE.recObjects) {
            INSTANCE.recObjects.add(obj);
        }
        synchronized (INSTANCE.recTrigger) {
            INSTANCE.recTrigger.notify();
            
        }
    }
    public static void stop() {
        INSTANCE.RecordThread.interrupt();
    }
    public void write(Object obj) throws IOException {
        if (!INSTANCE.enabled) {
            return;
        }
        if (obj instanceof FIM) {
            int[] words = ((FIM) obj).getWords();
            ByteBuffer bb = ByteBuffer.allocate(Short.BYTES+words.length * Short.BYTES);
            bb.putShort((short)((FIM)obj).getID());
            for (int i : words) {
                bb.putShort((short) i);
            }
            INSTANCE.write(Type.FIM, bb.array());
        } else if (obj instanceof FOM) {
            int[] words = ((FOM) obj).getWords();
            ByteBuffer bb = ByteBuffer.allocate(Short.BYTES+words.length * Short.BYTES);
            bb.putShort((short)((FOM)obj).getID());
            for (int i : words) {
                bb.putShort((short) i);
            }
            INSTANCE.write(Type.FOM, bb.array());
        } else if (obj instanceof BusMonitorMessage) { 
            BusMonitorMessage bm = ((BusMonitorMessage)obj);
            write(BM,bm.toBytes());
        } else if (obj instanceof HICFrame) {
            HICDataFrame hdf=((HICFrame)obj).getHdf();
            INSTANCE.write(((HICFrame)obj).isIsTIM()?HIM:HOM, hdf.getBytes());
        }
    }
    protected final LinkedList<Object> recObjects = new LinkedList<>();
    protected final Object recTrigger = new Object();
    
    protected final Thread RecordThread = new Thread("RECORDER") {
        @Override
        public void run() {
            while(!interrupted()) {
                LinkedList<Object> wlist;
                synchronized (recObjects) {
                    wlist = new LinkedList<>(recObjects);                    
                    recObjects.clear();
                }
                for(Object obj : wlist) {
                    try {
                        write(obj);
                    } catch (IOException ex) {
                    }
                }
                if(wlist.isEmpty()) {
                    try {
                        synchronized (recTrigger) {                            
                            recTrigger.wait(1000, 0);
                        }
                    } catch (InterruptedException ex) {
                        break;
                    }
                }
            }
            try {
                flush();
            } catch (IOException ex) {
                Logger.getLogger(Recorder.class.getName()).log(Level.SEVERE, null, ex);
            }
        }        
    };
    
            
    public static enum Type {
        HIM,
        HOM,
        FIM,
        FOM,
        BM,
        EXCEPTION,
        LOGENTRY;
    }
}
