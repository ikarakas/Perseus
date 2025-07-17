package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.DumpFile;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.data.DataFieldDecoder;
import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.data.DataFieldDictionary;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01.DataBlock;
import _int.nato.ncia.natxmlib.messages.tom1.NATOM01;
import _int.nato.ncia.natxmlib.monitor.MessageMonitor;
import _int.nato.ncia.natxmlib.monitor.ReceivedFrame;
import _int.nato.ncia.natxmlib.monitor.ReceivedMessage;
import _int.nato.ncia.natxmlib.types.Field;
import java.io.IOException;
import java.util.Comparator;
import java.util.Map;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.function.Consumer;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class TxMAnalyzer {
    protected static DataFieldDecoder dfdJTIDS_INIT;
    protected static DataFieldDecoder dfdJTIDS_STATUS;

    public static void onTxM(NATxM txm) {
        if (txm == null) {
            return;
        }
        if(txm instanceof NATIM01) {
            Map<String,Object> mmap=new TreeMap<String,Object>();
            NATIM01 tim01=(NATIM01)txm;
            for(DataBlock db : tim01.getDatablocks()) {
                Map<String,Object> map = dfdJTIDS_INIT.decode(db.getInitializationBlockId(), db.getStartingDataWord(), db.getDataWords());
                for(Map.Entry<String, Object> e : map.entrySet()) {
                    mmap.put(e.getKey(), e.getValue());
                }
            }
            for(Map.Entry<String, Object> e : mmap.entrySet()) {
                System.out.println("INIT_DATA_CHANGE_FIELD:"+e.getKey()+" = "+e.getValue().toString());
            }
            return;
        }
        if(txm instanceof NATOM01) {
            Map<String,Object> smap=new TreeMap<String,Object>();
            Map<String,Object> imap=new TreeMap<String,Object>();
            NATOM01 tom01=(NATOM01)txm;
            for(NATOM01.DataBlock db : tom01.getDatablocks()) {
                Map<String,Object> map = new TreeMap<>();
                if(db.getControlWord().isInitData()) {
                    map = dfdJTIDS_INIT.decode(db.getBlockId(), db.getStartingDataWord(), db.getDataWords());
                }else if(db.getControlWord().isStatusData()) {
                    map = dfdJTIDS_STATUS.decode(db.getBlockId(), db.getStartingDataWord(), db.getDataWords());                    
                }
                for(Map.Entry<String, Object> e : map.entrySet()) {
                    if(db.getControlWord().isInitData()) {
                        imap.put(e.getKey(), e.getValue());
                    }else if(db.getControlWord().isStatusData()) {
                        smap.put(e.getKey(), e.getValue());                        
                    }
                }
            }
            for(Map.Entry<String, Object> e : imap.entrySet()) {
                System.out.println("INIT_DATA_REPORT_FIELD:"+e.getKey()+" = "+e.getValue().toString());
            }
            for(Map.Entry<String, Object> e : smap.entrySet()) {
                System.out.println("STATUS_DATA_REPORT_FIELD:"+e.getKey()+" = "+e.getValue().toString());
            }
            return;
        }
    
        System.out.println("-------" + txm.getName() + "-------");
        for (Field f : txm.fields()) {
            System.out.println(f.toString());
        }
        System.out.println("\n-----------");
    }
    protected final static TreeSet<ReceivedMessage> messageSet = new TreeSet<>(new Comparator<ReceivedMessage>() {
        @Override
        public int compare(ReceivedMessage o1, ReceivedMessage o2) {
            int c0=o1.getReceiveTime().compareTo(o2.getReceiveTime());
            if(c0!=0) {
                return c0;
            }
            return Long.compare(o1.getSequenceNumber(), o2.getSequenceNumber());
        }
    });
    
    public static void onMessage(ReceivedMessage rm) {
        if (rm == null) {
            return;
        }
        if (rm.getMessage() == null) {
            return;
        }
        synchronized (messageSet) {
            messageSet.add(rm);            
        }
    }

    public static void main(String[] args) throws IOException {
        DataFieldDictionary.getInstance().addDefinitions(DataFieldDefinition.read("datafields.txt"));
        dfdJTIDS_INIT = new DataFieldDecoder(DataFieldDefinition.DataDomain.JTIDS_INITIALIZATION);
        dfdJTIDS_STATUS = new DataFieldDecoder(DataFieldDefinition.DataDomain.JTIDS_STATUS);
        SystemClock.getInstance().setReplayMode();
        String fileName="../dumps/dump_20220708_113018";
//        String fileName=(args.length==0)?"dump.txt":args[0];
        
        MessageMonitor mm = new MessageMonitor(new Consumer<ReceivedMessage>() {
            @Override
            public void accept(ReceivedMessage t) {
                onMessage(t);
            }
        });
        mm.start();
        try {
            for (DumpFile.Record r : DumpFile.parse(fileName)) {
                if (r.isTIM()) {
                    SystemClock.getInstance().setReplayTime(r.getTime());
                    mm.pushBIM(r);
                } else {
                    SystemClock.getInstance().setReplayTime(r.getTime());
                    mm.pushBOM(r);
                }
            }
        } catch (Exception ex) {
            Logger.getLogger(TxMAnalyzer.class.getName()).log(Level.SEVERE, null, ex);
        }
        mm.onEndOfData();
        for(ReceivedMessage rm : messageSet) {
            System.out.println(rm.getReceiveTime()+":"+rm.getMessage().getName());
            for(ReceivedFrame rf : rm.getFrames()) {
                System.out.println("     "+rf.getReceiveTime()+":"+rf.getFrame().toString());                
            }
            onTxM(rm.getMessage());
        }
    }
}
