package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.DumpFile;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSink;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import _int.nato.ncia.natxmlib.NATIMReader;
import _int.nato.ncia.natxmlib.messages.NATIM_Unknown;
import _int.nato.ncia.natxmlib.messages.NATIM_WRAP_AROUND;
import _int.nato.ncia.natxmlib.NATOMReader;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.codecs.NATxMStreamDecoder;
import _int.nato.ncia.natxmlib.conversion.JDataConverter;
import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.data.DataFieldDictionary;
import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01;
import _int.nato.ncia.natxmlib.messages.tim3.NATIM03;
import _int.nato.ncia.natxmlib.messages.tim4.NATIM04;
import _int.nato.ncia.natxmlib.messages.tom1.NATOM01;
import _int.nato.ncia.natxmlib.messages.tom3.NATOM03;
import _int.nato.ncia.natxmlib.time.MissionTimeFilter;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.TimeStampType;
import java.io.IOException;
import java.time.Instant;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.function.Consumer;
import java.util.logging.Level;
import java.util.logging.Logger;
import tdllib.link16.messages.Message;

/**
 *
 * @author mike
 */
public class TextDumpDecoder {

    public static void onTxM(NATxM txm) {
        if (txm == null) {
            return;
        }
        if (!(txm.isTIM() && (txm.getBlockId() == 1))) {
            return;
        }
        System.out.println("-------" + txm.getName() + "-------");
        for (Field f : txm.fields()) {
            System.out.println(f.toString());
        }
        System.out.println("\n-----------");
    }
    protected static void startEmulator(LinkedList<DumpFile.Record> bimList) throws IOException {
        FrameSource bimSource = new FrameSource(bimList);
/*        HICController hc;
        try {
            hc = HICController.create("/dev/ttyUSB0",9600,false);
        } catch (IOException ex) {
            Logger.getLogger(TextDumpDecoder.class.getName()).log(Level.SEVERE, null, ex);
            return;
        }
        JTIDSEmulator je = new JTIDSEmulator(bimSource, hc);
  */
        JTIDSEmulator je = new JTIDSEmulator(bimSource, new JTIDSDataFrameSink() {
            @Override
            public void write(JTIDSDataFrame frame) throws IOException {
                int y=10;
            }

            @Override
            public void close() {
            }
        });
        je.jtidsTerminalStatus.setInitDataComplete(false);
        je.jtidsTerminalStatus.setInitDataRequired(true);
        je.start();
        
    }
    protected static void startTOMMonitor(LinkedList<DumpFile.Record> bomList) {
        FrameSource bomSource = new FrameSource(bomList);
        JTIDSMonitor jm = new JTIDSMonitor(null,bomSource);
        jm.run();
/*        try {
            jm.initData.data.write("init.jdf");
        } catch (IOException ex) {
            Logger.getLogger(TextDumpDecoder.class.getName()).log(Level.SEVERE, null, ex);
        }
        try {
            //jm.initData.data.write("status.jdf");
        } catch (IOException ex) {
            Logger.getLogger(TextDumpDecoder.class.getName()).log(Level.SEVERE, null, ex);
        }
*/
        
    }
    protected static void startTIMMonitor(LinkedList<DumpFile.Record> bimList) {
        FrameSource bimSource = new FrameSource(bimList);
        JTIDSMonitor jm = new JTIDSMonitor(bimSource,null);
        jm.run();
/*        try {
            jm.initData.data.write("init.jdf");
        } catch (IOException ex) {
            Logger.getLogger(TextDumpDecoder.class.getName()).log(Level.SEVERE, null, ex);
        }
        try {
            //jm.initData.data.write("status.jdf");
        } catch (IOException ex) {
            Logger.getLogger(TextDumpDecoder.class.getName()).log(Level.SEVERE, null, ex);
        }
*/
        
    }
    public static void checkMissionTimes(LinkedList<DumpFile.Record> bimList) {
        FrameSource bimSource = new FrameSource(bimList);
        NATIMReader reader = new NATIMReader(bimSource);
        MissionTimeFilter mtf=new MissionTimeFilter();
        
        while (true) {
                NATxM tim;
                try {
                    tim = reader.read();
                } catch (IOException ex) {
                    Logger.getLogger(TextDumpDecoder.class.getName()).log(Level.SEVERE, null, ex);
                    break;
                }
                if (tim == null) {
                    break;
                }
                if (tim instanceof NATIM_WRAP_AROUND) {
                    continue;
                }
                if(tim instanceof NATIM04) {
                    Field f = ((NATIM04)tim).getField("TIME");
                    TimeStamp ts = (TimeStamp)f.getValue();
                    mtf.update(ts);
                    System.out.println(mtf.now());
                }
        }
    }
    public static void main(String[] args) throws IOException {
        DataFieldDictionary.getInstance().addDefinitions(DataFieldDefinition.read("datafields.txt"));
        SystemClock.getInstance().setReplayMode();
        
        LinkedList<DumpFile.Record> bimList = new LinkedList<>();
        LinkedList<DumpFile.Record> bomList = new LinkedList<>();

//        for (DumpFile.Record r : DumpFile.parse("../data/dump.txt")) {
        for (DumpFile.Record r : DumpFile.parse("../dumps/dump_20220823_133812")) {
            if (r.isTIM()) {
                bimList.add(r);
            }else{
                bomList.add(r);
            }
        }
        checkMissionTimes(bimList);
//        startEmulator(bimList);        
 //       startTOMMonitor(bomList);        
//        new TIMProcessor(new FrameSource(bimList)).run();
//         CoderTest.main(args);
//        AOCSModule.getInstance().close();
    }
    
    public static void main4(String[] args) throws IOException {
        LinkedList<DumpFile.Record> bimList = new LinkedList<>();
        LinkedList<DumpFile.Record> bomList = new LinkedList<>();

        for (DumpFile.Record r : DumpFile.parse("../dumps/dump.txt")) {
            if (r.isTIM()) {
                bimList.add(r);
            }else{
                bomList.add(r);
            }
        }
        FrameSource bimSource = new FrameSource(bimList);
        NATIMReader reader = new NATIMReader(bimSource);
        while (true) {
            try {
                NATxM tim = reader.read();
                if (tim == null) {
                    break;
                }
                if (tim instanceof NATIM_WRAP_AROUND) {
                    continue;
                }
                if(tim instanceof NATIM01) {
                    NATIM01 tim01=(NATIM01)tim;
                    for(NATIM01.DataBlock db : tim01.getDatablocks()) {
                        System.out.println("####IDB:"+db.toString());
                    }
                }
                if (tim instanceof NATIM03) {
                    
                } else if (tim instanceof NATIM_Unknown) {

                }
            } catch (Throwable t) {
                System.out.println(t);
            }
        }
        FrameSource bomSource=new FrameSource(bomList);
        NATOMReader tomReader = new NATOMReader(bomSource);
        while(true) {
            try {
                NATxM tom = tomReader.read();
                if(tom==null) {
                    break;
                }
                if(tom instanceof NATOM01) {
                    NATOM01 tom01=((NATOM01)tom);
                    for(NATOM01.DataBlock db : tom01.getDatablocks()) {
                        if(db.getControlWord().getResponseTypeCode()==2) {
                            int y=10;
                        }
                    }
                }
                if (tom instanceof NATOM03) {
                    for(Message msg : JDataConverter.decode(((NATOM03)tom).getData())) {
                        System.out.println(msg);
                    }
                    
                } 
            }catch(Throwable t) {
                System.out.println(t);                
            }
        }
    }

    public static class FrameSource implements JTIDSDataFrameSource {

        LinkedList<DumpFile.Record> list;
        Iterator<DumpFile.Record> iter;

        public FrameSource(LinkedList<DumpFile.Record> list) {
            this.list = list;
            this.iter = list.iterator();
        }

        @Override
        public JTIDSDataFrame read() throws IOException {
            if (!iter.hasNext()) {
                return null;
            } else {
                DumpFile.Record rec = iter.next();
                SystemClock.getInstance().setReplayTime(rec.getTime());
                //System.out.println(SystemClock.getInstance().now()+":FRAME:"+rec.toString());
                return rec;
            }
        }

        @Override
        public void close() {
        }

    }

    public static void main2(String[] args) throws IOException {
        System.out.println(Instant.now());
        NATxMStreamDecoder txmDecoder = new NATxMStreamDecoder(new Consumer<NATxM>() {
            @Override
            public void accept(NATxM t) {
                onTxM(t);
            }
        });
        for (DumpFile.Record r : DumpFile.parse("../dumps/dump.txt")) {
            System.out.println("#TIME:" + r.getTime());
            if (r.isTIM()) {
                if (r.getCode(0, 0, 1) == 1) {
                    System.out.println("WRAP AROUND TERMINAL INPUT");
                } else {
                    System.out.println("#TIM" + r.getCode(0, 1, 5));
                    txmDecoder.onTIM(r);
                }
            } else {
                if (r.getCode(0, 0, 1) == 1) {
                    System.out.println("WRAP AROUND TERMINAL OUTPUT");
                } else {
                    System.out.println("#TOM" + r.getCode(0, 1, 5));
                    txmDecoder.onTOM(r);
                }
            }

        }

//        HICController hicController = HICController.create("/dev/ttyUSB0");
        System.out.println("finished");

    }
}
