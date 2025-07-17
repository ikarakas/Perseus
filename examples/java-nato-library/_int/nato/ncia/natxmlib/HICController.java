/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib;

import _int.nato.ncia.ginslib.ntdlc.record.Recorder;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import com.fazecast.jSerialComm.SerialPort;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class HICController implements JTIDSDataFrameSink, JTIDSDataFrameSource {

    protected final SerialPort serialPort;
    protected final String serialDeviceName;
    protected final int baudRate;
    protected final int flowControlCode;
    protected BufferedWriter dumpWriter=null;

    private HICController(String serialDeviceName, int baudRate, boolean flowControl) throws IOException {
        if (serialDeviceName.toUpperCase().compareTo("AUTO")==0) {
            for (SerialPort sp : SerialPort.getCommPorts()) {
                serialDeviceName=sp.getSystemPortName();
                break;
            }
        }
        this.serialPort = SerialPort.getCommPort(serialDeviceName);
        if (serialPort == null) {
            throw new IOException("COM port \"" + serialDeviceName + "\" not found");
        }
        this.serialDeviceName = serialDeviceName;
//        this.flowControlCode=flowControl?(SerialPort.FLOW_CONTROL_CTS_ENABLED|SerialPort.FLOW_CONTROL_RTS_ENABLED|SerialPort.FLOW_CONTROL_DSR_ENABLED|SerialPort.FLOW_CONTROL_DTR_ENABLED):SerialPort.FLOW_CONTROL_DISABLED;
        this.flowControlCode = flowControl ? (SerialPort.FLOW_CONTROL_CTS_ENABLED | SerialPort.FLOW_CONTROL_RTS_ENABLED) : SerialPort.FLOW_CONTROL_DISABLED;
//        this.flowControlCode=flowControl?(SerialPort.FLOW_CONTROL_DTR_ENABLED|SerialPort.FLOW_CONTROL_DSR_ENABLED):SerialPort.FLOW_CONTROL_DISABLED;
        this.baudRate = baudRate;
        dumpWriter = null;

        init();
    }

    public static HICController create(String serialDeviceName, int baudRate, boolean flowControl) throws IOException {
        return new HICController(serialDeviceName, baudRate, flowControl);
    }
   
    public void setRecording(boolean enabled, String dumpPath) {
        if(enabled) {
            if(dumpWriter==null) {
                try {
                    DateTimeFormatter tdf = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");
                    Path dpath=Path.of(dumpPath);
                    Path dfile=dpath.resolve("dump_" + tdf.format(ZonedDateTime.now(ZoneId.of("UTC"))));
                    dumpWriter = new BufferedWriter(new FileWriter(dfile.toFile()));
                } catch (IOException ex) {
                    Logger.getLogger(HICController.class.getName()).log(Level.SEVERE, null, ex);
                }
            }
        }else{
            if(dumpWriter!=null) {
                try {
                    dumpWriter.close();
                } catch (IOException ex) {
                }
                dumpWriter=null;
            }
        }
    }
    private void readASYNC() {
        try {
            while (true) {
                while (serialPort.bytesAvailable() == 0) {
                    Thread.sleep(20);
                }

                byte[] readBuffer = new byte[serialPort.bytesAvailable()];
                int numRead = serialPort.readBytes(readBuffer, readBuffer.length);
//                System.out.println("Read " + numRead + " bytes.");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        serialPort.closePort();
    }

    private void readSYNC() {
        try {
            while (true) {
                byte[] readBuffer = new byte[1024];
                int numRead = serialPort.readBytes(readBuffer, readBuffer.length);
//                System.out.println(Instant.now() + ":read " + numRead + " bytes.");
            }
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            serialPort.closePort();
        }
    }

    private void writeSYNC(byte[] data) throws IOException {
        int wlen = serialPort.writeBytes(data, data.length);
    }

    private final void init() throws IOException {
        serialPort.setFlowControl(flowControlCode);
        serialPort.setBaudRate(baudRate);
        serialPort.setNumDataBits(8);
        serialPort.setParity(SerialPort.NO_PARITY);
        serialPort.setNumStopBits(1);
        serialPort.setComPortTimeouts(SerialPort.TIMEOUT_READ_BLOCKING, 500, 500);
        serialPort.setComPortTimeouts(SerialPort.TIMEOUT_WRITE_BLOCKING, 500, 500);
        if (!serialPort.openPort()) {
            throw new IOException("serial port cannot be opened");
        }
        serialPort.setDTR();
        //readASYNC();
    }
    //13:12:21.23071 -- TOM1 -- 20600002 345E0000 00000000  00000000 00000000 00000000  00000000 00000000 00008002 
    protected final static DateTimeFormatter dumpDTF = DateTimeFormatter.ofPattern("HH:mm:ss.SSSSS");

    public synchronized void dump(HICDataFrame hdf, boolean isTIM) throws IOException {
        Recorder.record(new HICFrame(hdf, isTIM));
        if (dumpWriter != null) {
            String line = dumpDTF.format(ZonedDateTime.now(ZoneId.of("UTC"))) + String.format(" -- T%sM%d -- ", (isTIM?"I":"O"),hdf.getCode(0, 1, 5)) + hdf.toString()+"\n";
            dumpWriter.write(line);
            dumpWriter.flush();
        }
    }
    public static class HICFrame  {
        protected final HICDataFrame hdf;
        protected final boolean isTIM;

        public HICFrame(HICDataFrame hdf, boolean isTIM) {
            this.hdf = hdf;
            this.isTIM = isTIM;
        }

        public HICDataFrame getHdf() {
            return hdf;
        }

        public boolean isIsTIM() {
            return isTIM;
        }
    }

    @Override
    public void write(JTIDSDataFrame frame) throws IOException {
        HICDataFrame hdf;
        if (frame instanceof HICDataFrame) {
            hdf = (HICDataFrame) frame;
        } else {
            hdf = HICDataFrame.create();
            for (int i = 0; i < 9; i++) {
                hdf.setWord(i, frame.getWord(i));
            }
        }
        writeSYNC(hdf.getBytes());
        dump(hdf, false);
    }

    @Override
    public void close() {
        serialPort.closePort();
    }
    protected Instant timeOfLastFrame = Instant.MIN;
    protected boolean initPhase=true;
    
    @Override
    public JTIDSDataFrame read() throws IOException {
        while (true) {
            byte[] readBuffer = new byte[HICDataFrame.BYTE_LENGTH];
            int dlen = 0;

            while (dlen < readBuffer.length) {
                int numRead = serialPort.readBytes(readBuffer, readBuffer.length - dlen, dlen);
                if (numRead < 0) {
                    throw new IOException();
                }
                dlen += numRead;
            }
            HICDataFrame hdf = HICDataFrame.fromBytes(readBuffer, 0, dlen);
            dump(hdf, true);
            Instant now=SystemClock.getInstance().now();
            Duration deltaT=Duration.between(timeOfLastFrame, now);
            if(deltaT.compareTo(Duration.ofSeconds(1))<0) {
                if(initPhase) {
                    System.out.println(SystemClock.getInstance().now() + ":HC:read:discared quick frame:"+hdf.toString());
                    timeOfLastFrame=now;
                    continue;
                }
            }else if(deltaT.compareTo(Duration.ofSeconds(21))>0) {
                System.out.println(SystemClock.getInstance().now() + ":HC:read:discared late frame:"+hdf.toString());
                initPhase=true;
                timeOfLastFrame=now;
                continue;                
            }
            initPhase=false;
            timeOfLastFrame=now;
            return hdf;
        }
    }
}
