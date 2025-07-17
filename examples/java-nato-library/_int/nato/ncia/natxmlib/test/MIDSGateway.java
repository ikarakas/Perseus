/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.ginslib.ntdlc.record.Recorder;
import _int.nato.ncia.ginslib.test.GINSProcessor;
import _int.nato.ncia.ginslib.test.UTCTimeFilter;
import _int.nato.ncia.natxmlib.Config;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSink;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import _int.nato.ncia.natxmlib.clock.OffsetClock;
import _int.nato.ncia.natxmlib.clock.SimpleClock;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.conversion.JDataConverter;
import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.data.DataFieldDictionary;
import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.gui.MIDSGatewayMonitorUI;
import _int.nato.ncia.natxmlib.jic.JICModule;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.common.JWordData;
import _int.nato.ncia.natxmlib.messages.common.SubgroupData;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01;
import _int.nato.ncia.natxmlib.messages.tim3.NATIM03;
import _int.nato.ncia.natxmlib.messages.tom3.NATOM03;
import _int.nato.ncia.natxmlib.messages.tom4.MessageStatusRecord;
import _int.nato.ncia.natxmlib.messages.tom4.NATOM04;
import _int.nato.ncia.natxmlib.nav.NAVMessage;
import _int.nato.ncia.natxmlib.nav.NAVModule;
import _int.nato.ncia.natxmlib.nav.TransmitFIM;
import aocslib.dataelements.Link16;
import fxmlib.data.mids.words.InitWord1;
import fxmlib.data.mids.words.InitWord1833;
import fxmlib.data.mids.words.InitWord1861;
import fxmlib.data.mids.words.InitWord3;
import fxmlib.data.mids.words.InitWord4;
import fxmlib.data.mids.words.StatusWord121;
import fxmlib.data.mids.words.StatusWord122;
import fxmlib.data.mids.words.StatusWord123;
import fxmlib.data.mids.words.StatusWord124;
import static fxmlib.fields.BitStatus.BIT_COMPLETED;
import static fxmlib.fields.BitStatus.BIT_IN_PROGRESS;
import fxmlib.fields.CurrentInitState;
import static fxmlib.fields.CurrentInitState.AWAITING_LOAD;
import static fxmlib.fields.CurrentInitState.LOAD_COMPLETE_DATA_CONFLICT;
import static fxmlib.fields.CurrentInitState.LOAD_COMPLETE_SEGMENT_COUNT_ERROR;
import static fxmlib.fields.CurrentInitState.LOAD_COMPLETE_VALIDITY_TEST_IN_PROGRESS;
import static fxmlib.fields.CurrentInitState.LOAD_COMPLETE_VALID_DATA;
import static fxmlib.fields.CurrentInitState.LOAD_IN_PROGRESS;
import static fxmlib.fields.NetEntryStatus.COARSE_SYNCHRONIZATION_ACHIEVED;
import static fxmlib.fields.NetEntryStatus.COARSE_SYNCHRONIZATION_CONFIRMED;
import static fxmlib.fields.NetEntryStatus.FINE_SYNCHRONIZATION_ACHIEVED;
import static fxmlib.fields.NetEntryStatus.NET_ENTRY_HAS_NOT_BEGUN;
import static fxmlib.fields.NetEntryStatus.NET_ENTRY_IN_PROGRESS;
import fxmlib.fields.TimeTag;
import fxmlib.fields.TransmitMode;
import fxmlib.fxm.FIM;
import fxmlib.fxm.FIM01;
import fxmlib.fxm.FIM02_CurrentInitDataRequest;
import fxmlib.fxm.FIM03_InitDataChange;
import fxmlib.fxm.FIM03_LoadComplete;
import fxmlib.fxm.FIM03_RestartLoadUsingCurrentData;
import fxmlib.fxm.FIM03_RestartLoadUsingDefaults;
import fxmlib.fxm.FIM30;
import fxmlib.fxm.FIM31;
import fxmlib.fxm.FOM;
import fxmlib.fxm.FOM01;
import fxmlib.fxm.FOM01_Link16;
import fxmlib.fxm.FOM02;
import fxmlib.fxm.FOM03;
import fxmlib.fxm.FOM04;
import fxmlib.fxm.FOM12;
import fxmlib.fxm.FOM17;
import fxmlib.fxm.FOM20;
import static fxmlib.mids.EngineState.FAILED;
import static fxmlib.mids.EngineState.FAILED_CONNECTING;
import static fxmlib.mids.EngineState.RUNNING;
import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.Year;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.temporal.ChronoField;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;
import java.util.TreeMap;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class MIDSGateway extends JTIDSEmulator {

    protected final MIDSModule midsModule = new MIDSModule(new Consumer<FOM>() {
        @Override
        public void accept(FOM t) {
            try {
                onFOM(t);
            } catch (Throwable th) {

            }
        }
    });
    protected final MIDSInitData midsInitData = new MIDSInitData();
    protected final InitDataChangeMapper initDataMapper = new InitDataChangeMapper(initData, midsInitData);

    protected final SimpleClock requestedNetworkClock = new OffsetClock(SystemClock.getInstance(), Duration.ofMinutes(0));
    protected final SimpleClock actualNetworkClock = new OffsetClock(SystemClock.getInstance());

    protected final NAVModule navModule = new NAVModule(new Consumer<>() {
        @Override
        public void accept(NAVMessage t) {
            onNAVMessage(t);
        }
    });
    protected final JICModule jicModule = JICModule.getInstance();

    public MIDSGateway() {
        super(JICModule.getInstance(), JICModule.getInstance());
    }

    public MIDSGateway(JTIDSDataFrameSource bimSource, JTIDSDataFrameSink bomSink) {
        super(bimSource, bomSink);
    }

    @Override
    public void start() throws IOException {
        super.sendPeriodicJTIDSStatus = false;
        super.start();
        jtidsClock.setBaseTime(null);
        navModule.start();
        midsModule.start();
        jicModule.start();
    }

    @Override
    public void stop() {
        navModule.stop();
        midsModule.stop();
        super.stop();
    }
    protected Instant lastFIM30Time = Instant.ofEpochMilli(0);
    protected Instant lastFIM31Time = Instant.ofEpochMilli(0);
    
    protected boolean isETRMode() {
        InitWord4 iw4 = InitWord4.fromCode(midsInitData.getWordData().getWord(0, 4));
        if (lastFOM03 != null) {
            if (iw4.getExternalTimeReference()) {
               if(!lastFOM03.isEtrnr()) {
                   switch(lastFOM03.getNetEntryStatus()) {
                       case NET_ENTRY_IN_PROGRESS:
                       case COARSE_SYNCHRONIZATION_ACHIEVED:
                       case COARSE_SYNCHRONIZATION_CONFIRMED:
                       case FINE_SYNCHRONIZATION_ACHIEVED:
                           return true;                           
                   }
               }
            }
        }
        return false;
    }
    protected Instant getMIDSNetworkTime() {
        if(isETRMode()) {
            return navModule.calculateUTC(SystemClock.getInstance().now());
        }else{
            return fom20TimeFilter.calculateUTC(SystemClock.getInstance().now());            
        }
    }
    protected void onNAVMessage(NAVMessage nm) {
        if (nm instanceof TransmitFIM) {
            try {
                if (((TransmitFIM) nm).getFim() instanceof FIM30) {
                    lastFIM30Time = SystemClock.getInstance().now();
                    FIM30 fim30=(FIM30)(((TransmitFIM) nm).getFim());
                    if(!Config.getInstance().isMidsNavUseUTC()) {
                        Instant networkTime=getMIDSNetworkTime();
                        if(networkTime!=null) {
                            fim30.getVelocityTimeOfValidity().setCode(GINSProcessor.toTimeTag(networkTime).getCode());
                        }else{
                            nm=null;
                        }
                    }
                } else if (((TransmitFIM) nm).getFim() instanceof FIM31) {
                    lastFIM31Time = SystemClock.getInstance().now();
                    FIM31 fim31=(FIM31)(((TransmitFIM) nm).getFim());
                    if(!Config.getInstance().isMidsNavUseUTC()) {
                        Instant networkTime=getMIDSNetworkTime();
                        if(networkTime!=null) {
                            fim31.getTimeTag().setCode(GINSProcessor.toTimeTag(networkTime).getCode());
                        }else{
                            nm=null;
                        }
                    }
                }
                if(nm!=null) {
                    midsModule.writeFIM(((TransmitFIM) nm).getFim());
                }
            } catch (IOException ex) {
                Recorder.record(ex);
            }
        }
    }

    @Override
    protected synchronized void writeTOM(NATxM tom) {
        if (midsModule.isOperational() && initDataRetrieved) {
            super.writeTOM(tom);
        }
    }
    protected final TreeMap<Integer, JSeriesTransmitEntry> tim03TransmitMap = new TreeMap<>();

    @Override
    protected void onTIM03(NATIM03 tim03) {
        if (lastFOM03 == null) {
            return;
        }
        if (lastFOM03.getNetEntryStatus() != FINE_SYNCHRONIZATION_ACHIEVED) {
            return;
        }
        Instant now = SystemClock.getInstance().now();
        Instant midsTime = fom20TimeFilter.calculateUTC(now);
        if (midsTime == null) {
            return;
        }
        ZonedDateTime zdt = ZonedDateTime.ofInstant(midsTime, ZoneId.of("UTC"));
        int millis = (zdt.getNano() / 1_000_000) % 1000;
        int micros = (zdt.getNano() / 1_000) % 1000;
        TimeTag tt = new TimeTag(zdt.getMinute(), zdt.getSecond(), millis, micros);
        FIM01 fim01 = JDataConverter.toFIM01(tim03, tt);
        try {
            midsModule.writeFIM(fim01);
        } catch (IOException ex) {
            return;
        }
        if (fim01.getMessageID() != 0) {
            JSeriesTransmitEntry jste = new JSeriesTransmitEntry(tim03, fim01, midsTime, now);
            JSeriesTransmitEntry prev;
            synchronized (tim03TransmitMap) {
                prev = tim03TransmitMap.put(fim01.getMessageID(), jste);
            }
            if ((prev != null) && !prev.wasProcessed()) {
                int y = 10;
            }

        }
        int y = 10;
    }
    protected final LinkedList<MessageStatusRecord> msrlist = new LinkedList<>();

    @Override
    protected MessageStatusRecord getNextMessageStatus() {
        synchronized (msrlist) {
            if (msrlist.isEmpty()) {
                return null;
            }
            return msrlist.removeFirst();
        }
    }
    protected Instant lastLink16TransmitTime = Instant.ofEpochMilli(0);

    protected void onFOM02(FOM02 fom02) {
        switch (fom02.getMessageStatus()) {
            case Message_Transmitted_Loopback_Fail:
            case Message_Transmitted_TOA_Comparison_Fail:
            case Message_Transmitted_no_Loopback:
            case Message_Transmitted_with_no_Errors:
                lastLink16TransmitTime = SystemClock.getInstance().now();
            default:
                break;
        }
        JSeriesTransmitEntry jste;
        synchronized (tim03TransmitMap) {
            jste = tim03TransmitMap.get(fom02.getMessageID());
        }
        if (jste == null) {
            return;
        }
        jste.update(fom02);
        Duration d = Duration.between(jste.systemForwardTime, SystemClock.getInstance().now());
        int size;
        synchronized (msrlist) {
            msrlist.add(new MessageStatusRecord(0, fom02.getMessageStatus().ordinal(), jste.tim03.getLoopbackId()));
            size = msrlist.size();
        }
        if (size >= 6) {
            transmitJTIDSTerminalStatus();
        }
        //System.out.println("####"+fom02.getMessageID()+";"+d+";"+fom02.getMessageStatus().toString());
    }

    @Override
    protected void onRestartLoad(boolean useDefault) {
        initDataConfirmed = true;
    }

    @Override
    protected void onLoadComplete(int blkCount) {
        //do not do anything here
    }

    @Override
    protected void onAOCSLink16(Link16 l16) throws IOException {
        //do not do anything here
    }

    protected int loadSegmentCount = 0;
    protected boolean loadingTerminal = false;

    @Override
    protected void onTIM01(NATIM01 tim01) {
        super.onTIM01(tim01);
        List<FIM> fim03List = initDataMapper.translate(tim01.getDatablocks());
        for (NATIM01.DataBlock db : tim01.getDatablocks()) {
//            System.out.println(SystemClock.getInstance().now() + ":JMG:JTIDS_INIT_DATA_CHANGE:blkId=" + db.getInitializationBlockId() + ", wrdId=" + db.getStartingDataWord() + ", cnt=" + db.getDataWords().length + ", words=" + toString(db.getDataWords()));

            if ((db.getInitializationBlockId() == 0) && (db.getStartingDataWord() == 2)) {
                int command = (db.getDataWords()[0] >> 14) & 0x3;
                switch (command) {
                    case 1:
                        loadCompleteDeclared = true;
                        restartLoadCurrentRequested = false;
                        restartLoadDefaultRequested = false;
                        loadingTerminal = false;
                        //fim03List.add(new FIM03_LoadComplete(loadSegmentCount));
                        System.out.println(SystemClock.getInstance().now() + ":JMG:" + "Load Complete declared");
                        break;
                    case 2:
                        restartLoadCurrentRequested = true;
                        loadingTerminal = true;
                        loadSegmentCount = -1;
//                        fim03List.add(new FIM03_RestartLoadUsingCurrentData());
                        System.out.println(SystemClock.getInstance().now() + ":JMG:" + "Restart Load (current) requested");
                        break;
                    case 3:
//                        fim03List.add(new FIM03_RestartLoadUsingDefaults());
                        System.out.println(SystemClock.getInstance().now() + ":JMG:" + "Restart Load (default) requested");
                        restartLoadDefaultRequested = true;
                        loadingTerminal = true;
                        loadSegmentCount = -1;
                        break;
                    default:
                        break;
                }
            }
        }
        for (FIM fim : fim03List) {
            if (fim instanceof FIM03_InitDataChange) {
                FIM03_InitDataChange idc = (FIM03_InitDataChange) fim;
                System.out.println(SystemClock.getInstance().now() + ":JMG:MIDS_INIT_DATA_CHANGE:wordId=" + idc.getStartDataWord() + ", cnt=" + idc.getDataWordCount());
            }
        }
        try {
            midsModule.writeBIM(fim03List);
            if (loadingTerminal) {
                loadSegmentCount += fim03List.size();
            }
        } catch (IOException ex) {
            Logger.getLogger(MIDSGateway.class.getName()).log(Level.SEVERE, null, ex);
        }
    }

    protected CurrentInitState currentInitState = CurrentInitState.NO_STATEMENT;
    protected Instant lastFOM03Time = Instant.MIN;
    protected boolean initDataRetrieved = false;
    protected boolean initDataConfirmed = false;

    protected boolean initDataRequestPending = false;

    protected FOM03 lastFOM03 = null;

    protected Instant timeOfLastFOM03 = Instant.MIN;
    protected boolean ltti=false;
    
    protected void onFOM03(FOM03 fom03) throws IOException {
        boolean requestMIDSInitData = false;
        Instant now = SystemClock.getInstance().now();

        if (Duration.between(lastFOM03Time, SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(5)) > 0) {
            initDataRetrieved = false;
            currentInitState = CurrentInitState.NO_STATEMENT;
        }
        boolean initStateChanged = currentInitState != fom03.getCurrentinitstate();

        if (initStateChanged && (fom03.getCurrentinitstate() == CurrentInitState.LOAD_COMPLETE_VALID_DATA)) {
            requestMIDSInitData = true;
            initDataRetrieved = false;
            loadCompleteDeclared = false;
            Arrays.fill(buffersAvailableSupported, false);
        }
        if (requestMIDSInitData) {
            System.out.println(SystemClock.getInstance().now() + ":JMG:" + "Retrieving Initialization Data Load from MIDS");
            initDataRequestPending = true;
            for (int i = 1; i < 1 + 63 * 30; i += 30) {
                try {
                    midsModule.writeFIM(new FIM02_CurrentInitDataRequest(0, i, 30));
                } catch (IOException ex) {
                    initDataRequestPending = false;
                    Logger.getLogger(MIDSModule.class.getName()).log(Level.SEVERE, null, ex);
                    break;
                }
            }
        }
        lastFOM03Time = now;
        lastFOM03 = fom03;
        currentInitState = fom03.getCurrentinitstate();
        ltti=fom03.isLtti();
        
        JTIDSTerminalStatus jts = getJTIDSTerminalStatus();

        switch (fom03.getNetEntryStatus()) {
            case NET_ENTRY_HAS_NOT_BEGUN:
                jts.setSyncStatus(NATOM04.SyncStatus.NET_ENTRY_NOT_IN_PROGRESS);
                break;
            case NET_ENTRY_IN_PROGRESS:
                jts.setSyncStatus(NATOM04.SyncStatus.COARSE_SYNC_IN_PROGRESS);
                break;
            case COARSE_SYNCHRONIZATION_CONFIRMED:
                jts.setSyncStatus(NATOM04.SyncStatus.COARSE_SYNC_IN_PROGRESS);
                break;
            case COARSE_SYNCHRONIZATION_ACHIEVED:
                jts.setSyncStatus(NATOM04.SyncStatus.COARSE_SYNC_ACHIEVED);
                break;
            case FINE_SYNCHRONIZATION_ACHIEVED:
                if(!fom03.isLtti())  {
                    jts.setSyncStatus(NATOM04.SyncStatus.FINE_SYNC_ACHIEVED);
                }else{
                    jts.setSyncStatus(NATOM04.SyncStatus.COARSE_SYNC_ACHIEVED);                    
                }
                break;
        }
        switch (fom03.getCurrentinitstate()) {
            case AWAITING_LOAD:
                jts.setInitDataComplete(false);
//                jts.setInitDataRequired(true);
                jts.setInitDataRequired(false);
                jts.setInitDataConflict(false);
                jts.setInitDataError(false);
                break;
            case LOAD_IN_PROGRESS: {
                jts.setInitDataComplete(false);
                jts.setInitDataRequired(false);
                jts.setInitDataConflict(false);
                jts.setInitDataError(false);
                break;
            }
            case LOAD_COMPLETE_VALIDITY_TEST_IN_PROGRESS: {
                jts.setInitDataComplete(false);
                jts.setInitDataRequired(false);
                jts.setInitDataConflict(false);
                jts.setInitDataError(false);
                break;
            }
            case LOAD_COMPLETE_VALID_DATA: {
                jts.setInitDataComplete(initDataRetrieved);
                jts.setInitDataRequired(initDataRetrieved && !loadCompleteDeclared);
                jts.setInitDataConflict(false);
                jts.setInitDataError(false);
                break;
            }
            case LOAD_COMPLETE_DATA_CONFLICT: {
                jts.setInitDataComplete(true);
                jts.setInitDataRequired(false);
                jts.setInitDataConflict(true);
                jts.setInitDataError(false);
                break;
            }
            case LOAD_COMPLETE_SEGMENT_COUNT_ERROR: {
                jts.setInitDataComplete(true);
                jts.setInitDataRequired(false);
                jts.setInitDataConflict(false);
                jts.setInitDataError(true);
                break;
            }
            default: {
                jts.setInitDataComplete(false);
                jts.setInitDataRequired(false);
                jts.setInitDataConflict(false);
                jts.setInitDataError(false);
                break;
            }
        }
        switch (fom03.getBitstatus()) {
            case BIT_COMPLETED:
                jts.setBitInProgress(false);
                break;
            case BIT_IN_PROGRESS:
                jts.setBitInProgress(true);
                break;
        }
        jts.setIpfFail(fom03.isIpff());
        jts.setTerminalFail(fom03.isTf());
        jts.setSduAlert(fom03.isNkl() | sduAlert);
        
        transmitJTIDSTerminalStatus();
    }

    @Override
    protected void transmitPeriodicJTIDSTerminalStatus() {
        //only when FOM03 trigger it
    }
    protected FOM17 lastFOM17 = null;
    protected Instant lastFOM17Time = Instant.ofEpochMilli(0);

    protected void onFOM17(FOM17 fom) {
        lastFOM17 = fom;
        lastFOM17Time = SystemClock.getInstance().now();
    }

    protected OffsetClock midsClock = new OffsetClock(SystemClock.getInstance(), Duration.ZERO);
    protected UTCTimeFilter fom20TimeFilter = new UTCTimeFilter();

    protected FOM20 lastFOM20 = null;
    protected Instant lastFOM20time = Instant.MIN;
    protected boolean midsTimeOK = false;
    protected boolean midsChronoTimeOK = false;

    protected boolean canSetTerminalTime() {
        if (lastFOM03 != null) {
            if (lastFOM03.getCurrentinitstate() == LOAD_COMPLETE_VALID_DATA) {
                if (lastFOM03.getNetEntryStatus() == NET_ENTRY_HAS_NOT_BEGUN || lastFOM03.getNetEntryStatus() == NET_ENTRY_IN_PROGRESS) {
                    return true;
                }
            }
        }
        return false;
    }
    protected void setTerminalTime() {
        Instant now = SystemClock.getInstance().now();
        Instant utc = navModule.calculateUTC(now);
        if (canSetTerminalTime()) {
            int diff = 1_000_000_000 - utc.getNano();
            new TimeSetterThread(utc.plus(Duration.ofNanos(diff))).start();
        }
    }
    protected class TimeSetterThread extends Thread {
        protected final Instant utc;

        public TimeSetterThread(Instant utc) {
            this.utc = utc;
        }

        @Override
        public void run() {
            Instant now = SystemClock.getInstance().now();
            Instant cutc = navModule.calculateUTC(now);
            Duration stime = Duration.between(cutc, utc);
            if (!stime.isNegative()) {
                try {
                    TimeUnit.NANOSECONDS.sleep(stime.toNanosPart());
                } catch (InterruptedException ex) {
                    Logger.getLogger(MIDSGateway.class.getName()).log(Level.SEVERE, null, ex);
                }
            }
            try {
                midsModule.setDateTime(utc);               
            } catch (IOException ex) {
                Logger.getLogger(MIDSGateway.class.getName()).log(Level.SEVERE, null, ex);
            }

        }
    }
    
    protected void onFOM20(FOM20 fom) {
        Instant now = SystemClock.getInstance().now();

        lastFOM20 = fom;
        lastFOM20time = now;

        Instant day;
        Instant mids_day = null;

        boolean requireTimeUpdate = false;
        Instant utc = navModule.calculateUTC(now);
        Instant utc_day = null;
        Duration utc_timeOfDay = null;
        if (utc != null) {
            ZonedDateTime zdt = ZonedDateTime.ofInstant(utc, ZoneId.of("UTC"));
            utc_day = zdt.toLocalDate().atStartOfDay(ZoneId.of("UTC")).toInstant();
            utc_timeOfDay = Duration.between(utc_day, utc);
            int y = 10;
        }
        if ((fom.getDayOfYear() != 0) && (fom.getYear() != 0)) {
            Year year = Year.of(fom.getYear());
            LocalDate ld = year.atDay(fom.getDayOfYear());
            ZonedDateTime zdt = ld.atStartOfDay(ZoneId.of("UTC"));
            day = mids_day = zdt.toInstant();
        } else {
            ZonedDateTime zdt = ZonedDateTime.ofInstant(now, ZoneId.of("UTC"));
            day = zdt.toLocalDate().atStartOfDay(ZoneId.of("UTC")).toInstant();
            requireTimeUpdate = true;
        }
        Duration mids_timeOfDay = Duration.ofHours(fom.getHour()).plusMinutes(fom.getMinute()).plusSeconds(fom.getSecond());
        Instant midsTime = day.plus(mids_timeOfDay);

        Duration preOffset=fom20TimeFilter.getOffset();
        fom20TimeFilter.update(midsTime, now);
        Duration fom20Offset = fom20TimeFilter.getOffset();
        
//        System.out.println("#MIDS_TIME:"+midsTime+",utc="+utc+",lastErr="+fom20TimeFilter.getLastError()+", ofs="+fom20Offset);

        Duration utcOffset = navModule.getUTCOffset();
        //System.out.println("#TIME_OFFSETS;"+fom20Offset+";"+utcOffset);

        if (utc_timeOfDay != null) {
            Duration deltaT = mids_timeOfDay.minus(utc_timeOfDay);
            //System.out.println("#MIDS_UTC_TIME_DELTA:"+deltaT);
            if ((deltaT.abs().compareTo(Duration.ofMillis(500)) >= 0) || (mids_day == null)) {
                try {
                    if (lastFOM03 != null) {
                        if (lastFOM03.getCurrentinitstate() == LOAD_COMPLETE_VALID_DATA) {
                            if (lastFOM03.getNetEntryStatus() == NET_ENTRY_HAS_NOT_BEGUN || lastFOM03.getNetEntryStatus() == NET_ENTRY_IN_PROGRESS) {
//                                System.out.println(now + ":JMG:MIDS_TIME_UPDATE:delta="+deltaT+" ,old=" + midsTime + ", new=" + utc);
                                if (1 == 0) {
                                    midsModule.setDateTime(utc);
                                    fom20TimeFilter.reset();
                                }
                            }
                        }
                    }
                } catch (IOException ex) {
                    Logger.getLogger(MIDSGateway.class.getName()).log(Level.SEVERE, null, ex);
                }
            }
        }
        Duration offset = Duration.between(now, midsTime);

        if (fom20Offset != null) {
            midsClock.setOffset(fom20Offset.negated());
            Instant f20time=fom20TimeFilter.calculateUTC(now);
            long secsOfDay = (f20time.getEpochSecond() % 86_400L);
            int nano = f20time.getNano();
            Instant base=now.minusSeconds(secsOfDay).minusNanos(nano);
            jtidsClock.setBaseTime(base);
        }
    }
    protected Duration midsTOD = null;
    protected Instant midsTODTime = Instant.MIN;
    protected Duration chronoTime = null;
    protected Instant chronoTimeTime = Instant.MIN;

    protected final boolean forwardMIDS_TSB = true;
    protected final boolean forwardMIDS_InitData = true;

    protected boolean sduAlert=false;
    protected TransmitMode midsTransmitMode = TransmitMode.NORMAL;
    
    protected void onFOM04(FOM04 fom04) {
        Instant now = SystemClock.getInstance().now();
//        System.out.println(now + ":JMG:" + "FOM04:sdw="+fom04.getStartDataWord()+", cnt="+fom04.getDataWordCount());
        if (fom04.isCurrentInitDataRequest()) {
//            System.out.println("#IDR:"+fom04.getStartDataWord()+";"+fom04.getLength());

            int[] fom04InitData = new int[fom04.getDataWordCount()];
            for (int i = 0; i < fom04InitData.length; i++) {
                fom04InitData[i] = fom04.getDataWord(i);
            }
            if (forwardMIDS_InitData) {
                initDataMapper.updateInitDataFromMIDS(fom04.getStartDataWord(), fom04InitData);
            }
            if ((fom04.getDataWordCount() == 30) && (fom04.getStartDataWord() == 1861)) {
                initDataRetrieved = true;
                initDataRequestPending=false;
                System.out.println(now + ":JMG:" + "Initialization data retrieved");
                jtidsTerminalStatus.setInitDataComplete(true);
                jtidsTerminalStatus.setInitDataRequired(true);
                transmitJTIDSTerminalStatus();
            }
            for (int i = 0; i < fom04InitData.length; i++) {
                if (!forwardMIDS_TSB) {
                    continue;
                }
                int midsWordNumber = fom04.getStartDataWord() + i;
                if(midsWordNumber==1) {
                    InitWord1 iw1 = InitWord1.fromCode(fom04InitData[i]);
                    midsTransmitMode=iw1.getTransmitMode();
                    continue;
                }
                
                if (midsWordNumber < 61) {
                    break;
                }
                if (midsWordNumber > 444) {
                    break;
                }
                int tsbDataWordNumber = midsWordNumber - 61;
                int tsb = tsbDataWordNumber / 6;
                int tsb_ofs = tsbDataWordNumber % 6;
                int blockId = 3 + tsb / 5;
                int wordId = 2 + (tsbDataWordNumber % 30);
                int oldJTIDSValue = initData.getWord(blockId, wordId);
                int newJTIDSValue = fom04InitData[i];
                if (oldJTIDSValue != newJTIDSValue) {
                    initData.setWord(blockId, wordId, fom04.getDataWord(i));
                }
                //System.out.println(now + ":JMG:FOM04:tsb="+tsb+",tsbOfs="+tsb_ofs+",tsbdwd="+tsbDataWordNumber+",mwid:"+midsWordNumber+", blkId="+blockId+", wordId="+wordId+", value="+String.format("0x%04x",newJTIDSValue)+", blockChanged="+initDataChanged);
            }
        } else if (fom04.isStatusDataRequest()) {
//            System.out.println("#SDR:"+fom04.getStartDataWord()+";"+fom04.getLength());
            if ((fom04.getStartDataWord() == 121) && (fom04.getDataWordCount() >= 4)) {
                StatusWord121 sw121 = StatusWord121.fromCode(fom04.getDataWord(0));
                StatusWord122 sw122 = StatusWord122.fromCode(fom04.getDataWord(1));
                StatusWord123 sw123 = StatusWord123.fromCode(fom04.getDataWord(2));
                StatusWord124 sw124 = StatusWord124.fromCode(fom04.getDataWord(3));
                midsTOD = Duration.ofHours(sw121.getHours()).plus(Duration.ofMinutes(sw121.getMinutes())).plus(Duration.ofSeconds(sw122.getSeconds()).plus(Duration.ofMillis((int) (sw122.getSlots() * 7.8125))));
                chronoTime = Duration.ofDays(sw124.getDays()).plus(Duration.ofHours(sw124.getHours())).plus(Duration.ofMinutes(sw124.getMinutes())).plus(Duration.ofSeconds(sw123.getSeconds()).plus(Duration.ofMillis((int) (sw123.getSlots() * 7.8125))));
                midsTODTime = chronoTimeTime = now;
                if (requestedNetworkClock.isRunning()) {
                    Instant requiredNetTime = requestedNetworkClock.now();
                    ZonedDateTime zdt = ZonedDateTime.ofInstant(requiredNetTime, ZoneId.of("UTC"));
                    ZonedDateTime chronoBaseTime = ZonedDateTime.of(zdt.getYear(), zdt.getMonthValue(), zdt.getDayOfMonth(), 0, 0, 0, 0, ZoneId.of("UTC"));
                    ZonedDateTime fullChronoTime = chronoBaseTime.plus(Duration.ofHours(sw124.getHours())).plus(Duration.ofMinutes(sw124.getMinutes())).plus(Duration.ofSeconds(sw123.getSeconds()).plus(Duration.ofMillis((int) (sw123.getSlots() * 7.8125))));
                    if (Math.abs(Duration.between(fullChronoTime.toInstant(), requiredNetTime).toSeconds()) < 5) {
                        midsChronoTimeOK = true;
                    } else {
                        midsChronoTimeOK = false; 
                    }
                } else {
                    midsChronoTimeOK = false;
                }
            }else{
                for(int i=0;i<fom04.getDataWordCount();i++) {
                    int wdata=fom04.getWord(0);
                    switch(fom04.getStartDataWord()+i) {
                        case 7:  {
                            sduAlert=((wdata >> 8) & 0x1)!=0;
                            jtidsTerminalStatus.setSduAlert(sduAlert);
                            break;
                        }
                    }
                }
            }
        }
    }

    @Override
    protected int getAvailableTransmitBuffers(int npg) {
        if(buffersAvailableSupported[npg]) {
            return buffersAvailable[npg];            
        }else{
            return super.getAvailableTransmitBuffers(npg); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/OverriddenMethodBody            
        }
    }
    protected int[] buffersAvailable = new int[512];
    protected boolean[] buffersAvailableSupported = new boolean[512];
    
    protected void onFOM12(FOM12 fom12) {
        for (FOM12.Entry e : fom12.getEntries()) {
            int npg=e.getPgIndexNumber() & 0x1ff;
            if(e.getNumberOfBuffersAvailable()>0) {
                buffersAvailableSupported[npg]=true;
            }
            buffersAvailable[npg] = e.getNumberOfBuffersAvailable();
        }
    }
    protected Instant lastFOM01Time=Instant.ofEpochMilli(0);
    protected void onFOM01(FOM01_Link16 fom01) {
        lastFOM01Time=SystemClock.getInstance().now();
        JWordData[] jwd = JDataConverter.toJWordData(fom01.getLink16Words());
        SubgroupData[] sg = JDataConverter.toSubgroupData(jwd);
        NATOM03 tom03 = NATOM03.create(fom01.getSTN(), fom01.getRXSlot() & 0x1ff, getCurrentJTIDSTime(), sg);
        if(isHostActive()) {
            writeTOM(tom03);
        }
    }

    @Override
    protected TimeStamp getCurrentJTIDSTime() {
        if(!useHostTime) {
            return jtidsClock.getCurrentMissionTime();
        }
        if(hostClock.getBaseTime()==null) {
            return jtidsClock.getCurrentMissionTime();            
        }
        return hostClock.getCurrentMissionTime();
    }
    protected boolean useHostTime=false;
    
    @Override
    protected void onTIM04_HostTime(TimeStamp hostTime, boolean timeSyncRequired) {
        hostClock.update(hostTime);
        if (timeSyncRequired) {
            useHostTime=true;
            System.out.println(SystemClock.getInstance().now() + ":JMG:TIME_SYNC_REQUEST:" + hostTime + " /TSR:" + timeSyncRequired);
        }
    }

    protected void onFOM(FOM fom) throws IOException {
        Recorder.record(fom);
        if (fom instanceof FOM03) {
            onFOM03((FOM03) fom);
        } else if (fom instanceof FOM01) {
            if (fom instanceof FOM01_Link16) {
                onFOM01((FOM01_Link16) fom);
            }
        } else if (fom instanceof FOM20) {
            onFOM20((FOM20) fom);
        } else if (fom instanceof FOM17) {
            onFOM17((FOM17) fom);
        } else if (fom instanceof FOM04) {
            onFOM04((FOM04) fom);
        } else if (fom instanceof FOM12) {
            onFOM12((FOM12) fom);
        } else if (fom instanceof FOM02) {
            onFOM02((FOM02) fom);
        }
    }

    public static void main(String[] args) throws IOException {
        CommandLineArguments cla = new CommandLineArguments();
        cla.parse(args);
        Config.getInstance().load(cla.getOptionValue("config", "ntdlc.conf"));

        DataFieldDictionary.getInstance().addDefinitions(DataFieldDefinition.read("datafields.txt"));

        Recorder.getInstance().setEnabled(Config.getInstance().isRecordingEnabled());

        MIDSGateway mg = new MIDSGateway();
        //MIDSGatewayGUI gui = new MIDSGatewayGUI(mg);
        MIDSGatewayMonitorUI mgmui = new MIDSGatewayMonitorUI(mg);
        mg.start();
        //gui.setVisible(true);
        mgmui.setVisible(true);
    }

    public class Controller {

        protected String fom20_DateString;
        protected String fom20_TimeString;

        public String initState() {
            if (lastFOM03 != null) {
                return lastFOM03.getCurrentinitstate().toString();
            } else {
                return "";
            }
        }

        public String syncState() {
            if (lastFOM03 != null) {
                return lastFOM03.getNetEntryStatus().toString();
            } else {
                return "";
            }
        }

        public boolean isMIDSTimeOK() {
            return midsTimeOK;
        }

        public boolean isNTR() {
            InitWord3 iw3 = InitWord3.fromCode(midsInitData.getWordData().getWord(0, 3));
            return iw3.getNtr();
        }

        public boolean isETR() {
            InitWord4 iw4 = InitWord4.fromCode(midsInitData.getWordData().getWord(0, 4));
            return iw4.getExternalTimeReference();
        }

        public boolean isETROK() {
            if (lastFOM03 != null) {
                return !lastFOM03.isEtrnr();
            } else {
                return true;
            }
        }

        public String getTerminalDate() {
            if (lastFOM20 == null) {
                return "";
            }
            if ((lastFOM20.getDayOfYear() != 0) && (lastFOM20.getYear() != 0)) {
                Year year = Year.of(lastFOM20.getYear());
                LocalDate ld = year.atDay(lastFOM20.getDayOfYear());
                LocalDateTime ldt = ld.atStartOfDay();
                ZonedDateTime zdt = ldt.atZone(ZoneId.of("UTC"));
                return String.format("%02d.%02d.%04d", zdt.get(ChronoField.DAY_OF_MONTH), zdt.get(ChronoField.MONTH_OF_YEAR), zdt.get(ChronoField.YEAR));
            } else {
                return "?";
            }
        }

        public String getTerminalTime() {
            Instant midsTime = fom20TimeFilter.calculateUTC(SystemClock.getInstance().now());
            if (midsTime == null) {
                return "";
            }
            ZonedDateTime zdt = ZonedDateTime.ofInstant(midsTime, ZoneId.of("UTC"));
            return String.format("%02d:%02d:%02d", zdt.get(ChronoField.HOUR_OF_DAY), zdt.get(ChronoField.MINUTE_OF_HOUR), zdt.get(ChronoField.SECOND_OF_MINUTE));

        }

        public String getUTCTime() {
            Instant utc = navModule.getUTCClock().now();
            if (utc == null) {
                return "";
            }
            ZonedDateTime zdt = ZonedDateTime.ofInstant(utc, ZoneId.of("UTC"));
            return String.format("%02d:%02d:%02d", zdt.get(ChronoField.HOUR_OF_DAY), zdt.get(ChronoField.MINUTE_OF_HOUR), zdt.get(ChronoField.SECOND_OF_MINUTE));
        }

        public String getUTCDate() {
            Instant utc = navModule.getUTCClock().now();
            if (utc == null) {
                return "";
            }
            ZonedDateTime zdt = ZonedDateTime.ofInstant(utc, ZoneId.of("UTC"));
            return String.format("%02d.%02d.%04d", zdt.get(ChronoField.DAY_OF_MONTH), zdt.get(ChronoField.MONTH_OF_YEAR), zdt.get(ChronoField.YEAR));
        }

        public String midsTOD() {
            if (midsTOD == null) {
                return "?";
            }
            int hours = midsTOD.toHoursPart();
            int mins = midsTOD.toMinutesPart();
            int sec = midsTOD.toSecondsPart();
            int millis = midsTOD.toMillisPart();

            return String.format("%02d:%02d:%02d.%03d", hours, mins, sec, millis);
        }
        
        public String chronoTime() {
            if (chronoTime == null) {
                return "?";
            }
            int hours = chronoTime.toHoursPart();
            int mins = chronoTime.toMinutesPart();
            int sec = chronoTime.toSecondsPart();
            int millis = chronoTime.toMillisPart();
            int day = (int) chronoTime.toDaysPart();
            return String.format("%02d:%02d:%02d.%03d [day %02d]", hours, mins, sec, millis, day);
        }

        public String terminalConnectionStatus() {
            if (midsModule.isOperational()) {
                return "Active";
            } else {
                return "Connecting";
            }
        }

        public void doResetLoad() {
            try {
//                midsModule.writeFIM(new FIM03_DeleteSet(0));
                midsModule.writeFIM(new FIM03_RestartLoadUsingCurrentData());
            } catch (IOException ex) {
                Logger.getLogger(MIDSGateway.class.getName()).log(Level.SEVERE, null, ex);
            }
        }

        public void doRestartLoad(boolean defaults) {
            try {
                if (defaults) {
                    midsModule.writeFIM(new FIM03_RestartLoadUsingDefaults());
                    midsModule.writeFIM(new FIM03_LoadComplete(0));
                    //initData.data.read("_init.jdf");
                } else {
                    midsModule.writeFIM(new FIM03_RestartLoadUsingCurrentData());
                    midsModule.writeFIM(new FIM03_LoadComplete(0));
                    //initData.data.read("init.jdf");
                }

            } catch (IOException ex) {
                Logger.getLogger(MIDSGateway.class.getName()).log(Level.SEVERE, null, ex);
            }
        }

        public void doNetEntryReset(boolean ntr, boolean etr, boolean timesync, boolean startNetEntry) {
            LinkedList<FIM> fimList = new LinkedList<>();
            if (timesync) {
                try {
                    Instant now = SystemClock.getInstance().now();
                    Instant utc = navModule.calculateUTC(now);
                    if (utc != null) {
                        midsModule.setDateTime(utc);
                    }
                } catch (IOException ex) {
                    Logger.getLogger(MIDSGateway.class.getName()).log(Level.SEVERE, null, ex);
                }
            }
            InitWord4 iw4 = InitWord4.fromCode(midsInitData.getWordData().getWord(0, 4));
            iw4.setExternalTimeReference(etr);
            fimList.add(new FIM03_InitDataChange(0, 4, new int[]{iw4.getCode()}));

            InitWord3 iw3 = InitWord3.fromCode(midsInitData.getWordData().getWord(0, 3));
            iw3.setNtr(ntr);
            fimList.add(new FIM03_InitDataChange(0, 3, new int[]{iw3.getCode()}));

            InitWord1833 iw1833 = InitWord1833.fromCode(midsInitData.getWordData().getWord(0, 1833));
            iw1833.setNetEntryReset(true);
            fimList.add(new FIM03_InitDataChange(0, 1833, new int[]{iw1833.getCode()}));

            InitWord1861 iw1861 = InitWord1861.fromCode(midsInitData.getWordData().getWord(0, 1861));
            iw1861.setStartNetEntry(startNetEntry);
            fimList.add(new FIM03_InitDataChange(0, 1861, new int[]{iw1861.getCode()}));

            try {
                midsModule.writeBIM(fimList);
            } catch (IOException ex) {
                Logger.getLogger(MIDSGateway.class.getName()).log(Level.SEVERE, null, ex);
            }
            midsInitData.getWordData().setWord(0, 3, iw3.getCode());
            midsInitData.getWordData().setWord(0, 4, iw4.getCode());
        }
        public void doSetTerminalTime() {
            setTerminalTime();
        }
        public boolean checkCanSetTerminalTime() {
            return canSetTerminalTime();
        }
    }
    public final Controller controller = new Controller();

    public class Monitor {

        public State getState(Component comp) {
            switch (comp) {
                case MIDS_LINK: {
                    switch (midsModule.getEngineState()) {
                        case CREATED:
                            return State.NOP;
                        case RUNNING:
                            return State.OP;
                        case FAILED:
                        case FAILED_CONNECTING:
                            return State.FAIL;
                        default:
                            return State.INI;
                    }
                }
                case MIDS_LOAD: {
                    if (getState(Component.MIDS_LINK) != State.OP) {
                        return State.NOP;
                    }
                    if (lastFOM03 != null) {
                        switch (lastFOM03.getCurrentinitstate()) {
                            case LOAD_COMPLETE_VALIDITY_TEST_IN_PROGRESS:
                            case AWAITING_LOAD:
                            case LOAD_IN_PROGRESS:
                                return State.INI;
                            case LOAD_COMPLETE_DATA_CONFLICT:
                            case LOAD_COMPLETE_SEGMENT_COUNT_ERROR:
                                return State.FAIL;
                            case LOAD_COMPLETE_VALID_DATA:
                                return State.OP;
                            default:
                                return State.NOP;

                        }
                    } else {
                        return State.NOP;
                    }
                }
                case MIDS_CRYPTO: {
                    if (getState(Component.MIDS_LINK) != State.OP) {
                        return State.NOP;
                    }
                    if (lastFOM03 != null) {
                        if (lastFOM03.isNkl()) {
                            return State.FAIL;
                        }
                        if(sduAlert) {
                            return State.FAIL;
                        }
                        return State.OP;
                    } else {
                        return State.INI;
                    }
                }
                case MIDS_SYNC: {
                    if (getState(Component.MIDS_LINK) != State.OP) {
                        return State.NOP;
                    }

                    if (lastFOM03 != null) {
                        switch (lastFOM03.getNetEntryStatus()) {
                            case COARSE_SYNCHRONIZATION_ACHIEVED:
                            case NET_ENTRY_IN_PROGRESS:
                            case COARSE_SYNCHRONIZATION_CONFIRMED:
                                return State.INI;
                            case FINE_SYNCHRONIZATION_ACHIEVED:
                                return State.OP;

                        }
                    }
                    return State.NOP;
                }
                case JIC: {
                    if (jicModule.isJICConnected()) {
                        return State.OP;
                    } else {
                        return State.INI;
                    }
                }
                case CPS: {
                    if (getState(Component.JIC) == State.FAIL) {
                        return State.FAIL;
                    }
                    if (isCPSLinkActive()) {
                        return State.OP;
                    } else {
                        return State.INI;
                    }
                }
                case MOCP: {
                    if (getState(Component.JIC) == State.FAIL) {
                        return State.FAIL;
                    }

                    if (isHostActive()) {
                        return State.OP;
                    } else {
                        return State.INI;
                    }
                }
                case GINS_LINK: {
                    if (navModule.isMilBusOpen()) {
                        if (navModule.isMilBusActive()) {
                            return State.OP;
                        } else {
                            return State.INI;
                        }
                    } else {
                        if (navModule.isMilBusFail()) {
                            return State.FAIL;
                        } else {
                            return State.INI;
                        }
                    }
                }
                case GPS: {
                    if (navModule.isMilBusActive()) {
                        if (navModule.isGPSActive()) {
                            return State.OP;
                        } else {
                            return State.INI;
                        }
                    } else {
                        return State.FAIL;
                    }
                }
                case UTC: {
                    if (navModule.isMilBusActive()) {
                        if (navModule.isUTCActive()) {
                            return State.OP;
                        } else {
                            return State.INI;
                        }
                    } else {
                        return State.FAIL;
                    }
                }
                case NAV: {
                    if (navModule.isMilBusActive()) {
                        if (navModule.isNAVActive()) {
                            return State.OP;
                        } else {
                            return State.INI;
                        }
                    } else {
                        return State.FAIL;
                    }
                }
                case MIDS_NAV: {
                    if (getState(Component.MIDS_LINK) != State.OP) {
                        return State.NOP;
                    }
                    if (lastFOM17 != null) {
                        if (Duration.between(lastFOM17Time, SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(2)) < 0) {
                            if (lastFOM17.getGeoHorizPositionQuality().getValue() > 5) {
                                return State.OP;
                            } else {
                                return State.INI;
                            }
                        } else {
                            return State.FAIL;
                        }
                    } else {
                        return State.FAIL;
                    }
                }
                case L16_TX: {
                    if (lastFOM03 != null) {
                        if(lastFOM03.getNetEntryStatus()!=FINE_SYNCHRONIZATION_ACHIEVED) {
                            return State.NOP;                            
                        }
                        if (lastFOM03.isLtti()) {
                            return State.NOP;
                        }
                        if(midsTransmitMode==TransmitMode.CONDITIONAL_RADIO_SILENCE) {
                            return State.NOP;
                        }                        
                    }else{
                        return State.NOP;
                    }
                    if (Duration.between(lastLink16TransmitTime, SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(12)) < 0) {
                        return State.OP;
                    }else{
                        return State.INI;
                    }
                }
                case L16_RX: {
                    if (lastFOM03 != null) {
                        switch(lastFOM03.getNetEntryStatus()) {
                            case NET_ENTRY_HAS_NOT_BEGUN:
                            case NET_ENTRY_IN_PROGRESS:
                                return State.NOP;
                        }
                    }else{
                        return State.NOP;
                    }
                    if (Duration.between(lastFOM01Time, SystemClock.getInstance().now()).compareTo(Duration.ofSeconds(12)) < 0) {
                        return State.OP;
                    }else{
                        return State.INI;
                    }
                }
                case MIDS_TIME: {
                    if(lastFOM20!=null) {
                        if((lastFOM20.getDayOfMonth()==0) || (lastFOM20.getDayOfYear()==0) || (lastFOM20.getYear()==0)) {
                            return State.FAIL;
                        }
                    }else{
                         return State.NOP;
                    }
                    
                    Instant utc = navModule.getUTCClock().now();
                    if(utc==null) {
                        return State.INI;
                    }
                    Instant mt = fom20TimeFilter.calculateUTC(SystemClock.getInstance().now());
                    if(mt==null) {
                        return State.INI;
                    }
                    Duration deltaT=Duration.between(mt,utc);
                    if(deltaT.abs().compareTo(Duration.ofMillis(800))>=0) {
                        return State.FAIL;
                    }
                    return State.OP;
                }
                case UTC_TIME: {
                    Instant utc = navModule.getUTCClock().now();
                    if (utc == null) {
                        return State.FAIL;
                    } else {
                        return State.OP;
                    }

                }
            }

            int state = (int) (Math.round(Math.random() * 4));
            return State.values()[state % 4];
        }
    }

    public final Monitor monitor = new Monitor();

    public static enum Component {
        MIDS_LINK,
        MIDS_LOAD,
        MIDS_NAV,
        MIDS_SYNC,
        MIDS_CRYPTO,
        JIC,
        CPS,
        MOCP,
        NAV,
        GINS_LINK,
        GPS,
        UTC,
        L16_RX,
        L16_TX,
        MIDS_TIME,
        UTC_TIME
    }

    public static enum State {
        NOP,
        INI,
        OP,
        FAIL;
    }

    protected class JSeriesTransmitEntry {

        protected final NATIM03 tim03;
        protected final FIM01 fim01;
        protected final Instant networkForwardTime;
        protected final Instant systemForwardTime;
        protected FOM02 fom02 = null;
        protected Instant networkTransmitTime = null;

        public JSeriesTransmitEntry(NATIM03 tim03, FIM01 fim01, Instant networkForwardTime, Instant systemForwardTime) {
            this.tim03 = tim03;
            this.fim01 = fim01;
            this.networkForwardTime = networkForwardTime;
            this.systemForwardTime = systemForwardTime;
        }

        public boolean wasProcessed() {
            return fom02 != null;
        }

        public void update(FOM02 fom02) {
            this.fom02 = fom02;
        }
    }
}
