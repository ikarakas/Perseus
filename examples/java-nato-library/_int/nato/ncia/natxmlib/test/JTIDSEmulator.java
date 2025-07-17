/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.Config;
import _int.nato.ncia.natxmlib.HICController;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSink;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import _int.nato.ncia.natxmlib.NATIMReader;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.conversion.JDataConverter;
import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.data.DataFieldDictionary;
import _int.nato.ncia.natxmlib.data.JTIDSStatusDataGenerator;
import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.gui.JTIDSEmulatorGui;
import _int.nato.ncia.natxmlib.messages.NATIM_WRAP_AROUND;
import _int.nato.ncia.natxmlib.messages.NATOM_WRAP_AROUND;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.common.JWordData;
import _int.nato.ncia.natxmlib.messages.common.SubgroupData;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01.DataBlock;
import _int.nato.ncia.natxmlib.messages.tim3.NATIM03;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM04;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM4_RequestReplyRecord;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM4_RequestRepyRecord_Reply;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM4_RequestRepyRecord_Request;
import _int.nato.ncia.natxmlib.messages.tom1.NATOM01;
import _int.nato.ncia.natxmlib.messages.tom3.NATOM03;
import _int.nato.ncia.natxmlib.messages.tom4.MessageStatusRecord;
import _int.nato.ncia.natxmlib.messages.tom4.NATOM04;
import _int.nato.ncia.natxmlib.time.MissionTimeFilter;
import _int.nato.ncia.natxmlib.types.Field;
import aocslib.DataElement;
import aocslib.MulticastClass;
import aocslib.dataelements.Link16;
import aocslib.dataelements.Link16Word;
import aocslib.net.MASETransmitSocket;
import com.fazecast.jSerialComm.SerialPort;
import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import tdllib.common.datafields.DataItemException;
import tdllib.link16.data.Link16WordData;
import tdllib.link16.datafields.ActiveRelayIndicator;
import tdllib.link16.datafields.AirPlatform;
import tdllib.link16.datafields.AirPlatformActivity;
import tdllib.link16.datafields.AirborneIndicator;
import tdllib.link16.datafields.Altitude13;
import tdllib.link16.datafields.AltitudeQuality;
import tdllib.link16.datafields.BailoutIndicator;
import tdllib.link16.datafields.C2Indicator;
import tdllib.link16.datafields.Course;
import tdllib.link16.datafields.EmergencyIndicator;
import tdllib.link16.datafields.ExerciseIndicator;
import tdllib.link16.datafields.FlightLeaderIndicator;
import tdllib.link16.datafields.ForceTellIndicator;
import tdllib.link16.datafields.GeodeticPositionQuality;
import tdllib.link16.datafields.Latitude23;
import tdllib.link16.datafields.Longitude24;
import tdllib.link16.datafields.MessageLengthIndicator;
import tdllib.link16.datafields.MissionCommanderIndicator;
import tdllib.link16.datafields.Mode_III_Code;
import tdllib.link16.datafields.Mode_II_Code;
import tdllib.link16.datafields.Mode_I_Code;
import tdllib.link16.datafields.NetNumber;
import tdllib.link16.datafields.NonStsA;
import tdllib.link16.datafields.NpsIndicator;
import tdllib.link16.datafields.RttReplyStatusIndicator;
import tdllib.link16.datafields.SimulationIndicator;
import tdllib.link16.datafields.Speed;
import tdllib.link16.datafields.Strength;
import tdllib.link16.datafields.TimeQuality;
import tdllib.link16.messages.J2_2;
import tdllib.link16.words.J2_2_C1_Word;
import tdllib.link16.words.J2_2_E0_Word;
import tdllib.link16.words.J2_2_I_Word;

/**
 *
 * @author mike
 */
public class JTIDSEmulator {

    protected final JTIDSDataFrameSource bimSource;
    protected final JTIDSDataFrameSink bomSink;

    public JTIDSEmulator(JTIDSDataFrameSource bimSource, JTIDSDataFrameSink bomSink) {
        this.bimSource = bimSource;
        this.bomSink = bomSink;
    }
    protected Thread readerThread;
    protected Thread writerThread;
    protected Thread statusThread;

    protected int session = 19;
    protected String multicastInterface = "0.0.0.0";

    protected MASETransmitSocket aocsSocket;

    protected JTIDSEmulator withSession(int session) {
        this.session = session;
        return this;
    }
    protected Thread aocsReceiveThread;

    protected JTIDSInitData initData = new JTIDSInitData();
    protected JTIDSStatusDataGenerator statusDataGenerator = new JTIDSStatusDataGenerator();

    protected MissionTimeFilter hostClock = new MissionTimeFilter();
    protected MissionTimeFilter jtidsClock = new MissionTimeFilter();

    protected boolean sendPeriodicJTIDSStatus=true;
   
    public void start() throws IOException {
        aocsSocket = new MASETransmitSocket(session, MulticastClass.RAP, multicastInterface);

        initData.data.read("current.jdf");
        initData.setWord(63, 5, 0);
        initData.setWord(0, 2, 0);

        statusDataGenerator.data.read("status.jdf");

        readerThread = new Thread(new ReaderRunnable());
        readerThread.setName("TIMReader");
        if (sendPeriodicJTIDSStatus) {
            statusThread = new Thread(jtidsTerminalStatusRunnable);
            statusThread.setName("StatusTransmitter");
        }
        aocsReceiveThread = new Thread(new AOCSReceiveRunnable());
        aocsReceiveThread.setName("AOCSRXThread");

        Instant now = SystemClock.getInstance().now();
        long secondOfDay = now.getEpochSecond() % 86_400;
        long firstSecondOfToday = now.getEpochSecond() - secondOfDay;
        jtidsClock.setBaseTime(Instant.ofEpochSecond(firstSecondOfToday));

        readerThread.start();
        if (sendPeriodicJTIDSStatus) {
            statusThread.start();
        }
        //aocsReceiveThread.start();
    }

    public void stop() {
        statusThread.interrupt();
        readerThread.interrupt();
        aocsReceiveThread.interrupt();
        aocsSocket.close();
    }

    public static String toString(int[] words) {
        StringBuilder sb = new StringBuilder();
        sb.append("[");
        for (int i = 0; i < words.length; i++) {
            sb.append(String.format("0x%04x", words[i]));
            if (i < words.length - 1) {
                sb.append(",");
            }
        }
        sb.append("]");
        return sb.toString();
    }
    protected boolean cpsLinkFailure = false;

    
    protected boolean isCPSLinkActive() {
        return !cpsLinkFailure && Duration.between(lastTIMTime, SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(15)) < 0;
    }

    protected boolean isHostActive() {
        return isCPSLinkActive() && Duration.between(lastTIM04Time, SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(15)) < 0;
    }

    protected synchronized void writeTOM(NATxM tom) {
        if(!isCPSLinkActive()) {
//            return;
        }
        JTIDSDataFrame[] frames = tom.encode();
        for (JTIDSDataFrame frame : frames) {
            try {
                bomSink.write(frame);
            } catch (IOException ex) {
                Logger.getLogger(JTIDSEmulator.class.getName()).log(Level.SEVERE, null, ex);
                cpsLinkFailure = true;
                break;
            }
            cpsLinkFailure = false;
        }
    }
    protected final JTIDSTerminalStatus jtidsTerminalStatus = new JTIDSTerminalStatus();
    protected final JTIDSTerminalStatusRunnable jtidsTerminalStatusRunnable = new JTIDSTerminalStatusRunnable();

    public JTIDSTerminalStatus getJTIDSTerminalStatus() {
        return jtidsTerminalStatus;
    }
    //---------------------------------- TIM01 ---------------------------------------------
    protected boolean restartLoadCurrentRequested = false;
    protected boolean restartLoadDefaultRequested = false;
    protected boolean loadCompleteDeclared = false;
    protected boolean netEntryResetRequested = false;

    protected void onRestartLoad(boolean useDefault) {
        restartLoadCurrentRequested = !useDefault;
        restartLoadDefaultRequested = useDefault;
        try {
            if (useDefault) {
                initData.data.read("default.jdf");
                System.out.println(SystemClock.getInstance().now() + ":JTE:loaded default init data from file");
            } else {
                initData.data.read("current.jdf");
                System.out.println(SystemClock.getInstance().now() + ":JTE:loaded current init data from file");
            }
        } catch (IOException ex) {
            Logger.getLogger(JTIDSEmulator.class.getName()).log(Level.SEVERE, null, ex);
        }
    }

    protected void onLoadComplete(int blkCount) {
        loadCompleteDeclared = true;
    }
    protected boolean requireTOM04 = false;

    protected void onNetEntryReset() {
        netEntryResetRequested = true;
    }

    protected void change_InitDataWord(int blkId, int wordId, int value) {
        switch (blkId) {
            case 0: {
                switch (wordId) {
                    case 2: {
                        int command = (value >> 14) & 0x3;
                        int blkCount = (value & 0x3f);
                        System.out.println(SystemClock.getInstance().now() + ":JTE:TERMINAL LOAD:COMMAND=" + command);
                        switch (command) {
                            case 1:
                                onLoadComplete(blkCount);
                                break;
                            case 2:
                                onRestartLoad(false);
                                break;
                            case 3:
                                onRestartLoad(true);
                                break;
                            default:
                                break;
                        }
                    }
                    break;
                }
            }
            break;
            case 63: {
                switch (wordId) {
                    case 5: {
                        if ((value & 0x001) != 0) {
                            onNetEntryReset();
                        }
                    }
                    break;
                }
            }
            break;
        }
        initData.setWord(blkId, wordId, value);
    }

    protected void onTIM01_InitDataChange_sendResponse(int startDataBlockId, int startDataWord, int[] words) {
        if (jtidsTerminalStatus.isInitDataRequired()) {
            return;
        }
        NATOM01 response = null;
        boolean specialTOM = false;
        if (startDataBlockId == 1) {
            for (int i = startDataWord; i < startDataWord + 4; i++) {
                if ((i == 2) || (i == 4)) {
                    specialTOM = true;
                    break;
                }
            }
        } else if (startDataBlockId == 0) {
            if (startDataWord == 2) {
                int command = (words[0] >> 14) & 0x3f;
                if (command == 2) { //restart_current
                    response = NATOM01.generateTOM01_InitDataResponse(0, 2, new int[]{0, 0x8000});
                } else if (command == 3) { //restart_default
                    response = NATOM01.generateTOM01_InitDataResponse(0, 2, new int[]{0, 0xc000});
                }
            }
        }
        if (specialTOM) { // ICD 10.2.4.2.1
            int lastWord = startDataWord + words.length;
            int[] data = initData.getWords(startDataBlockId, 2, lastWord - 2);
            response = NATOM01.generateTOM01_InitDataResponse(1, 2, data);
        }
        if (response == null) {
            int[] data = initData.getWords(startDataBlockId, startDataWord, words.length);
            response = NATOM01.generateTOM01_InitDataResponse(startDataBlockId, startDataWord, data);
        }
        if (response != null) {
            writeTOM(response);
        }
    }

    protected void onTIM01_InitDataChange(int startDataBlockId, int startDataWord, int[] words) {
        System.out.println(SystemClock.getInstance().now() + ":JTE:INIT_DATA_CHANGE:blkId=" + startDataBlockId + ", wrdId=" + startDataWord + ", cnt=" + words.length);

        for (int i = 0; i < words.length; i++) {
            change_InitDataWord(startDataBlockId, i + startDataWord, words[i]);
        }
        onTIM01_InitDataChange_sendResponse(startDataBlockId, startDataWord, words);
        if (loadCompleteDeclared && ((!jtidsTerminalStatus.isInitDataComplete()) || (jtidsTerminalStatus.isInitDataRequired()))) {
            System.out.println(SystemClock.getInstance().now() + ":JTE:INIT_STATE_CHANGE: INIT DATA COMPLETE");
            jtidsTerminalStatus.setInitDataComplete(true);
            jtidsTerminalStatus.setInitDataRequired(false);
            jtidsTerminalStatusRunnable.trigger();
        }
    }

    protected void onTIM01_newCCCS() {
        double lat = initData.getCCCSLatitude();
        double lng = initData.getCCCSLongitude();
        double er_nm = initData.getCCCSEarthRadius();
        Map<String, Long> vmap = initData.getFieldCodes();
        Object latitude = initData.fieldView.getValue("CCCS LATITUDE");
        Object longtitude = initData.fieldView.getValue("CCCS LONGITUDE");
        Object earthRadius = initData.fieldView.getValue("CCCS EARTH RADIUS");
        jtidsTerminalStatus.newCCCSOriginAccepted = true;
        jtidsTerminalStatusRunnable.trigger();
    }

    protected void onTIM01(NATIM01 tim01) {
        if (tim01.isInitDataChange()) {
            for (DataBlock db : tim01.getDatablocks()) {
                onTIM01_InitDataChange(db.getInitializationBlockId(), db.getStartingDataWord(), db.getDataWords());
            }
        }
        if (tim01.hasNewCCSOrigin()) {
            onTIM01_newCCCS();
        }
    }
    //---------------------------------- TIM03 ---------------------------------------------

    protected void onTIM03(NATIM03 tim03) {
        Link16WordData[] l16data = JDataConverter.getLink16WordData(tim03.getData());
        Link16Word[] awords = JDataConverter.toAOCSLink16Words(l16data);
        Link16 l16de = new Link16(tim03.getSTN(), awords);
        AOCSModule.getInstance().transmit(l16de);
    }

    //---------------------------------- TIM04 ---------------------------------------------
    protected void onTIM04_HostTime(TimeStamp hostTime, boolean timeSyncRequired) {
        hostClock.update(hostTime);
        if (timeSyncRequired) {
            jtidsClock.setBaseTime(hostClock.getBaseTime());
        }
        System.out.println(SystemClock.getInstance().now() + ":JTE:HOSTIME:" + hostTime + " /TSR:" + timeSyncRequired);
    }

    protected int getAvailableTransmitBuffers(int npg) {
        return 20;
    }

    protected void onTIM04_StatusDataRequest(int startDataBlockId, int startDataWord, int dataWordCount) throws IOException {
        int[] data = statusDataGenerator.getWords(startDataBlockId, startDataWord, dataWordCount);
        if (startDataBlockId == 19) {
            for (int i = 0; i < data.length; i++) {
                int npg = 0;
                switch (startDataWord + i) {
                    case 13:
                        npg = initData.fieldView.getBigCode("NPG A FOR MESSAGE METERING").intValue();
                        break;
                    case 14:
                        npg = initData.fieldView.getBigCode("NPG B FOR MESSAGE METERING").intValue();
                        break;
                    case 15:
                        npg = initData.fieldView.getBigCode("NPG C FOR MESSAGE METERING").intValue();
                        break;
                    case 16:
                        npg = initData.fieldView.getBigCode("NPG D FOR MESSAGE METERING").intValue();
                        break;
                    case 17:
                        npg = initData.fieldView.getBigCode("NPG E FOR MESSAGE METERING").intValue();
                        break;
                    case 18:
                        npg = initData.fieldView.getBigCode("NPG F FOR MESSAGE METERING").intValue();
                        break;
                    case 19:
                        npg = initData.fieldView.getBigCode("NPG G FOR MESSAGE METERING").intValue();
                        break;
                    default:
                        break;
                }
                data[i] = npg << 8 | getAvailableTransmitBuffers(npg);
            }
        }
        NATxM tom01 = NATOM01.generateTOM01_StatusDataResponse(startDataBlockId, startDataWord, data);
        writeTOM(tom01);
//        System.out.println(SystemClock.getInstance().now() + ":JTE:STATUS_DATA_REQUEST:" + startDataBlockId + "," + startDataWord + "," + dataWordCount);
    }

    protected void onTIM04_InitDataRequest(int startDataBlockId, int startDataWord, int dataWordCount) throws IOException {
        int[] data = initData.getWords(startDataBlockId, startDataWord, dataWordCount);

        NATxM tom01 = NATOM01.generateTOM01_InitDataResponse(startDataBlockId, startDataWord, data);
        System.out.println(SystemClock.getInstance().now() + ":JTE:INIT_DATA_REQUEST:" + startDataBlockId + "," + startDataWord + "," + dataWordCount);
        writeTOM(tom01);

    }

    protected void onTIM04_Host_RC_Reply(int rcReplyCode, int rcLoopbackId) {
        int y = 10;
    }

    protected void onTIM04_Record(NATIM4_RequestReplyRecord rec) throws IOException {
        if (rec instanceof NATIM4_RequestRepyRecord_Request) {
            NATIM4_RequestRepyRecord_Request req = ((NATIM4_RequestRepyRecord_Request) rec);
            if (req.getAddressType() == NATIM4_RequestRepyRecord_Request.AddressTypeSpecifier.DATA_WORD_CODE) {
                if (req.getRequestType() == NATIM4_RequestRepyRecord_Request.RequestType.INITIALIZATION_REQUEST) {
                    onTIM04_InitDataRequest(req.getStartDataBlockId(), req.getStartDataWord(), req.getDataWordCount());
                } else if (req.getRequestType() == NATIM4_RequestRepyRecord_Request.RequestType.STATUS_REQUEST) {
                    onTIM04_StatusDataRequest(req.getStartDataBlockId(), req.getStartDataWord(), req.getDataWordCount());
                } else {
                    System.out.println("UNSUPPORTED REQUEST!");
                }
            }
        } else if (rec instanceof NATIM4_RequestRepyRecord_Reply) {
            onTIM04_Host_RC_Reply(((NATIM4_RequestRepyRecord_Reply) rec).getRCReplyCode(), ((NATIM4_RequestRepyRecord_Reply) rec).getRCLoopbackId());
        }

    }
    protected final PositionCalculator positionCalculator = new PositionCalculator();

    protected J2_2 buildPPLI(int pq, int aq) {
        try {

            J2_2_I_Word iword = new J2_2_I_Word(
                    MessageLengthIndicator.DATAITEM_1,
                    ExerciseIndicator.NON_EXERCISE_TRACK,
                    MissionCommanderIndicator.NOT_MISSION_COMMANDER,
                    ForceTellIndicator.NO_STATEMENT,
                    EmergencyIndicator.NO_STATEMENT,
                    C2Indicator.C2_UNIT,
                    SimulationIndicator.REAL_TRACK_UNIT,
                    AirborneIndicator.AIRBORNE,
                    FlightLeaderIndicator.NOT_FLIGHT_LEADER,
                    ActiveRelayIndicator.RELAYING_INACTIVE,
                    RttReplyStatusIndicator.DEFAULT,
                    NpsIndicator.ACTIVE_NON_SPECIFIC,
                    TimeQuality.LESS_THAN_1600_NS,
                    GeodeticPositionQuality.fromValue(pq),
                    Strength.ONE_UNIT,
                    BailoutIndicator.NO_STATEMENT,
                    Altitude13.fromFeet((int) (double) positionCalculator.getAltitude()),
                    NetNumber.DEFAULT,
                    NonStsA.ACTIVE,
                    AltitudeQuality.fromValue(aq));
            J2_2_E0_Word e0word = new J2_2_E0_Word(
                    Latitude23.fromDegrees((double) positionCalculator.getLatitude()),
                    Longitude24.fromDegrees(positionCalculator.getLongitude()),
                    Course.fromDegrees((int) (double) positionCalculator.getHeading()),
                    Speed.fromDmH(positionCalculator.getSpeed_DM_H()));
            J2_2_C1_Word c1word = new J2_2_C1_Word(Mode_I_Code.DEFAULT, Mode_II_Code.DEFAULT, Mode_III_Code.DEFAULT, AirPlatform.AIRBORNE_EARLY_WARNING_AND_CONTROL, AirPlatformActivity.AIRBORNE_EARLY_WARNING);
            J2_2 j22 = new J2_2(iword, e0word, c1word);
            return j22;
        } catch (DataItemException ex) {
            return null;
        }

    }

    protected void onTIM04_Position(TimeStamp ts, double lat, double lng, int alt, int pq, int aq) {
        positionCalculator.update(ts, lat, lng, alt, pq, aq);
        if (positionCalculator.getHeading() == null) {
            return;
        }
        J2_2 ppli = buildPPLI(pq, aq);
        if (ppli == null) {
            return;
        }

        Link16 l16de = new Link16(initData.getTerminalAddress(), JDataConverter.toAOCSLink16Words(ppli));
        AOCSModule.getInstance().transmit(l16de);

    }
    protected NATIM04 lastTIM04 = null;
    protected Instant lastTIM04Time = Instant.MIN;

    protected void onTIM04(NATIM04 tim04) throws IOException {
        lastTIM04 = tim04;
        lastTIM04Time = SystemClock.getInstance().now();

        TimeStamp ts = ((Field<TimeStamp>) (tim04.getField("TIME"))).getValue();
        onTIM04_HostTime(ts, tim04.getBoolean("TIME SYNC REQUIRED", false));
        onTIM04_Record(((Field<NATIM4_RequestReplyRecord>) tim04.getField("REQUEST_REPLY_1")).getValue());
        onTIM04_Record(((Field<NATIM4_RequestReplyRecord>) tim04.getField("REQUEST_REPLY_2")).getValue());
        onTIM04_Record(((Field<NATIM4_RequestReplyRecord>) tim04.getField("REQUEST_REPLY_3")).getValue());
        if (tim04.getBoolean("POSITION FIX VALID", false)) {
            double lat = (Double) (tim04.getField("LATITUDE").getValue());
            double lng = (Double) (tim04.getField("LONGITUDE").getValue());
            int alt = (Integer) (tim04.getField("ALTITUDE").getValue());
            int aq = (Integer) (tim04.getField("ALTITUDE QUALITY").getValue());
            int pq = (Integer) (tim04.getField("POSITION QUALITY").getValue());
            onTIM04_Position(ts, lat, lng, alt, pq, aq);
        }
    }
    protected Instant lastWRAPReceiveTime = Instant.MIN;
    protected Instant lastTIMTime = Instant.MIN;

    protected void onTIM(NATxM tim) throws Exception {
        lastTIMTime = SystemClock.getInstance().now();
        if (tim instanceof NATIM01) {
            onTIM01((NATIM01) tim);
        } else if (tim instanceof NATIM03) {
            onTIM03((NATIM03) tim);
        } else if (tim instanceof NATIM04) {
            onTIM04((NATIM04) tim);
        } else if (tim instanceof NATIM_WRAP_AROUND) {
            lastWRAPReceiveTime = SystemClock.getInstance().now();
            writeTOM(new NATOM_WRAP_AROUND((NATIM_WRAP_AROUND) tim));
        }
    }

    protected void onEndOfInput() {
        stop();
    }

    protected static HICController openHIC(String[] args) {
        CommandLineArguments cla = new CommandLineArguments();
        cla.parse(args);

        if (cla.contains("list")) {
            for (SerialPort port : SerialPort.getCommPorts()) {
                System.out.println(port.getSystemPortName());
            }
            return null;
        }

        String serialPortName;
        int baudRate = 115200;

        if (cla.contains("port")) {
            serialPortName = cla.getOptionValue("port", "undef");
        } else {
            SerialPort[] ports = SerialPort.getCommPorts();
            if (ports.length == 0) {
                System.err.println("no serial port found!");
                return null;
            }
            serialPortName = ports[0].getSystemPortName();
        }
        if (cla.contains("baud")) {
            baudRate = Integer.parseInt(cla.getOptionValue("baud", "115200"));
        }
        boolean handShake = Boolean.parseBoolean(cla.getOptionValue("handshake", "false"));

        HICController hc;
        try {
            hc = HICController.create(serialPortName, baudRate, handShake);
            return hc;
        } catch (IOException ex) {
            Logger.getLogger(TextDumpDecoder.class.getName()).log(Level.SEVERE, null, ex);
            return null;
        }

    }

    public static void main(String[] args) throws IOException {
        CommandLineArguments cla = new CommandLineArguments();
        cla.parse(args);
        Config.getInstance().load(cla.getOptionValue("config", "ntdlc.conf"));
        DataFieldDictionary.getInstance().addDefinitions(DataFieldDefinition.read("datafields.txt"));

        HICController hc = openHIC(args);
        if (hc == null) {
            return;
        }
        hc.setRecording(Config.getInstance().isJICDumpEnabled(), Config.getInstance().getRecordingPath());
        JTIDSEmulator je = new JTIDSEmulator(hc, hc);
        JTIDSEmulatorGui jeg = new JTIDSEmulatorGui(je);
        jeg.setVisible(true);
        je.start();
    }

    public class ReaderRunnable implements Runnable {

        NATIMReader reader = new NATIMReader(bimSource);

        @Override
        public void run() {
            while (!Thread.interrupted()) {
                NATxM tim = null;
                try {
                    tim = reader.read();
                    if (tim == null) {
                        break;
                    }
                } catch (IOException ex) {
                    Logger.getLogger(JTIDSEmulator.class.getName()).log(Level.SEVERE, null, ex);
                    break;
                } catch (IllegalArgumentException iaex) {
                    Logger.getLogger(JTIDSEmulator.class.getName()).log(Level.WARNING, null, iaex);
                }
                if (tim != null) {
                    try {
                        onTIM(tim);
                    } catch (IOException ex) {
                        Logger.getLogger(JTIDSEmulator.class.getName()).log(Level.SEVERE, null, ex);
                        break;

                    } catch (Exception ex) {
                        Logger.getLogger(JTIDSEmulator.class.getName()).log(Level.WARNING, null, ex);
                    }
                }
            }
            onEndOfInput();
        }
    }
    protected NATOM04 lastTOM04 = null;

    protected void transmitJTIDSTerminalStatus() {
        if(!isCPSLinkActive()) {
            //return;
        }        
        NATOM04 tom04 = jtidsTerminalStatus.buildTOM();
        if(tom04==null) {
            return;
        }
        writeTOM(tom04);
        lastTOM04 = tom04;
        if (isHostActive()) {
            if (jtidsTerminalStatus.isNewCCCSOriginAccepted()) {
                jtidsTerminalStatus.setNewCCCSOriginAccepted(false);
                System.out.println(SystemClock.getInstance().now() + ":JTE:NEW CCCS ACKNOWLEDGED");

            }
            if (jtidsTerminalStatus.isInitDataRequired()) {
                jtidsTerminalStatus.setInitDataRequired(false);
                System.out.println(SystemClock.getInstance().now() + ":JTE:IDR FLAG SENT AND RESET");
            }
        }
        jtidsTerminalStatus.setAocpInitRequest(false);
        jtidsTerminalStatus.setUserRefresh(false);
    }

    protected void transmitPeriodicJTIDSTerminalStatus() {
        transmitJTIDSTerminalStatus();
    }

    public class JTIDSTerminalStatusRunnable implements Runnable {

        protected final Object waitObject = new Object();

        public void trigger() {
            synchronized (waitObject) {
                waitObject.notify();
            }

        }

        @Override
        public void run() {
            while (!Thread.interrupted()) {
                transmitPeriodicJTIDSTerminalStatus();
                try {
//                    initData.data.write("init.jdf");
                } catch (Exception ex) {

                }
                try {
                    synchronized (waitObject) {
                        waitObject.wait(5000);
                    }
                } catch (InterruptedException ex) {
                    break;
                }
            }
        }
    }

    protected MessageStatusRecord getNextMessageStatus() {
        return null;
    }
    protected TimeStamp getCurrentJTIDSTime() {
        //return jtidsClock.getCurrentMissionTime();
        return hostClock.getCurrentMissionTime();
    }
    public class JTIDSTerminalStatus {

        protected NATOM04.SyncStatus syncStatus = NATOM04.SyncStatus.NET_ENTRY_NOT_IN_PROGRESS;
        protected boolean newCCCSOriginAccepted = false;
        protected boolean initDataComplete = false;
        protected boolean initDataRequired = false;
        protected boolean bitInProgress;
        protected boolean initDataError;
        protected boolean initDataConflict;
        protected boolean ipfFail;
        protected boolean sduAlert;
        protected boolean terminalFail;
        protected boolean userRefresh;
        protected boolean aocpInitRequest;

        public NATOM04 buildTOM() {
            NATOM04 tom04 = NATOM04.create();
            ((Field<NATOM04.SyncStatus>) tom04.getField("SYNC STATUS")).setValue(syncStatus);
            ((Field<Boolean>) tom04.getField("NEW CCCS ORIGIN ACCEPTED")).setValue(newCCCSOriginAccepted);
            ((Field<Boolean>) tom04.getField("INITIALIZATION COMPLETE")).setValue(initDataComplete);
            ((Field<Boolean>) tom04.getField("INITIALIZATION DATA ERROR")).setValue(initDataError);
            ((Field<Boolean>) tom04.getField("INITIALIZATION DATA REQUIRED")).setValue(initDataRequired);
            ((Field<Boolean>) tom04.getField("INITIALIZATION DATA CONFLICT")).setValue(initDataConflict);
            ((Field<Boolean>) tom04.getField("BIT IN PROGRESS")).setValue(bitInProgress);
            ((Field<Boolean>) tom04.getField("IPF FAIL")).setValue(ipfFail);
            ((Field<Boolean>) tom04.getField("SDU ALERT")).setValue(sduAlert);
            ((Field<Boolean>) tom04.getField("TERMINAL FAIL")).setValue(terminalFail);
            ((Field<Boolean>) tom04.getField("USER REFRESH")).setValue(userRefresh);
            ((Field<Boolean>) tom04.getField("INITIALIZATION FROM AOCP")).setValue(aocpInitRequest);
            TimeStamp ts = getCurrentJTIDSTime();
            if(ts==null) {
                return null;
            }
            ((Field<TimeStamp>) tom04.getField("TIME")).setValue(ts);
            for (int i = 1; i < 6; i++) {
                Field<MessageStatusRecord> fmsr = (Field<MessageStatusRecord>) (tom04.getField("STATUS_" + i));
                MessageStatusRecord msr = getNextMessageStatus();
                if (msr != null) {
                    fmsr.setValue(msr);
                } else {
                    fmsr.setCode(0);
                }
            }
//            System.out.println(SystemClock.getInstance().now() + ":TERMINAL_STATUS: TIME=" +ts.toString()+", SYNC="+syncStatus+" ,IC="+initDataComplete);

            return tom04;
        }

        public void setUserRefresh(boolean userRefresh) {
            this.userRefresh = userRefresh;
        }

        public void setAocpInitRequest(boolean aocpInitRequest) {
            this.aocpInitRequest = aocpInitRequest;
        }

        public NATOM04.SyncStatus getSyncStatus() {
            return syncStatus;
        }

        public void setSyncStatus(NATOM04.SyncStatus syncStatus) {
            this.syncStatus = syncStatus;
        }

        public boolean isInitDataComplete() {
            return initDataComplete;
        }

        public void setInitDataComplete(boolean initDataComplete) {
            this.initDataComplete = initDataComplete;
        }

        public boolean isInitDataRequired() {
            return initDataRequired;
        }

        public void setInitDataRequired(boolean initDataRequired) {
            this.initDataRequired = initDataRequired;
        }

        public boolean isBitInProgress() {
            return bitInProgress;
        }

        public void setBitInProgress(boolean bitInProgress) {
            this.bitInProgress = bitInProgress;
        }

        public boolean isInitDataError() {
            return initDataError;
        }

        public void setInitDataError(boolean initDataError) {
            this.initDataError = initDataError;
        }

        public boolean isIpfFail() {
            return ipfFail;
        }

        public void setIpfFail(boolean ipfFail) {
            this.ipfFail = ipfFail;
        }

        public boolean isSduAlert() {
            return sduAlert;
        }

        public void setSduAlert(boolean sduAlert) {
            this.sduAlert = sduAlert;
        }

        public boolean isTerminalFail() {
            return terminalFail;
        }

        public void setTerminalFail(boolean terminalFail) {
            this.terminalFail = terminalFail;
        }

        public boolean isInitDataConflict() {
            return initDataConflict;
        }

        public void setInitDataConflict(boolean initDataConflict) {
            this.initDataConflict = initDataConflict;
        }

        public boolean isNewCCCSOriginAccepted() {
            return newCCCSOriginAccepted;
        }

        public void setNewCCCSOriginAccepted(boolean newCCCSOriginAccepted) {
            this.newCCCSOriginAccepted = newCCCSOriginAccepted;
        }

        public void apply() {
            jtidsTerminalStatusRunnable.trigger();
        }
    }

    protected void onAOCSLink16(Link16 l16) throws IOException {
        if (l16.getSource() == 1) {
            return;
        }
        JWordData[] jwd = JDataConverter.toJWordData(l16.getWords());
        SubgroupData[] sg = JDataConverter.toSubgroupData(jwd);
        NATOM03 tom03 = NATOM03.create(l16.getSource(), 0, getCurrentJTIDSTime(), sg);
        
    }

    public class AOCSReceiveRunnable implements Runnable {

        @Override
        public void run() {
            while (!Thread.interrupted()) {
                try {
                    for (DataElement de : AOCSModule.getInstance().receive()) {
                        if (de instanceof Link16) {
                            onAOCSLink16((Link16) de);
                        }
                    }
                } catch (IOException ex) {
                    break;
                }
            }
        }
    }

    public class JTDISEmulatorController {

        public String getHostTime() {
            if (lastTIM04 == null) {
                return "";
            }
            return lastTIM04.getField("TIME").getValue().toString();
        }

        public String getTerminalTime() {
            if (lastTOM04 == null) {
                return "";
            }
            return lastTOM04.getField("TIME").getValue().toString();
        }

        public String getLinkState() {
            Instant now = SystemClock.getInstance().now();
            if (Duration.between(lastTIM04Time, now).compareTo(Duration.ofSeconds(15)) < 0) {
                return "Host active";
            }
            if (Duration.between(lastWRAPReceiveTime, now).compareTo(Duration.ofSeconds(15)) < 0) {
                return "Link active";
            }
            return "Inactive";
        }

        public void setSyncState(NATOM04.SyncStatus syncState) {
            initData.setWord(63, 5, initData.getWord(63, 5) & 0xfffe);
            netEntryResetRequested = false;
            restartLoadCurrentRequested = false;
            restartLoadDefaultRequested = false;
            loadCompleteDeclared = false;
            jtidsTerminalStatus.setSyncStatus(syncState);
        }

        public boolean isNetEntryReset() {
            return netEntryResetRequested;
        }

        public boolean isLoadCurrentRequested() {
            return restartLoadCurrentRequested;
        }

        public boolean isLoadDefaultsRequested() {
            return restartLoadDefaultRequested;
        }

        public boolean isLoadCompleteDeclared() {
            return loadCompleteDeclared;
        }

        public void doPauseOutput(boolean pause) {
        }

        public void doLoadInitData() {
            try {
                initData.data.read("current.jdf");
                System.out.println(SystemClock.getInstance().now() + ":JTE:loaded current init data");
            } catch (IOException ex) {
                Logger.getLogger(JTIDSEmulator.class.getName()).log(Level.SEVERE, null, ex);
            }
        }

        public void doStoreInitData() {
            try {
                initData.data.write("current.jdf");
                System.out.println(SystemClock.getInstance().now() + ":JTE:stored current init data");
            } catch (IOException ex) {
                Logger.getLogger(JTIDSEmulator.class.getName()).log(Level.SEVERE, null, ex);
            }
        }
    }
    public final JTDISEmulatorController jtidsEmulatorController = new JTDISEmulatorController();
}
