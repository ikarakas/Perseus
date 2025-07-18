/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.NATIMReader;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.conversion.JDataConverter;
import _int.nato.ncia.natxmlib.data.DataFieldDecoder;
import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01.DataBlock;
import _int.nato.ncia.natxmlib.messages.tim3.NATIM03;
import _int.nato.ncia.natxmlib.messages.tom3.NATOM03;
import _int.nato.ncia.natxmlib.test.TextDumpDecoder.FrameSource;
import aocslib.DataElementType;
import aocslib.Header;
import aocslib.MulticastClass;
import aocslib.dataelements.Link16;
import aocslib.dataelements.Link16Word;
import java.io.IOException;
import java.time.Instant;
import java.util.Map;
import java.util.Map.Entry;
import tdllib.link16.data.Link16WordData;
import tdllib.link16.messages.J3_2;
import tdllib.link16.messages.Message;

/**
 *
 * @author mike
 */
public class TIMProcessor implements Runnable {
    protected final FrameSource bimSource;

    protected JTIDSInitData initData = new JTIDSInitData();
    protected DataFieldDecoder dfd = new DataFieldDecoder(DataFieldDefinition.DataDomain.JTIDS_INITIALIZATION);
    
    public TIMProcessor(FrameSource bimSource) {
        this.bimSource = bimSource;
    }
    protected void setInitDataWord(int blockId, int wordId, int word) {
        //System.out.println("SET_INIT_DATA: blockId="+blockId+" ,wordId="+wordId+", value="+String.format("%04X", word));
    }
    public void onInitDataChange(int blockId, int startingDataWord, int[] words) {
        for(int i=0;i<words.length;i++) {
            setInitDataWord(blockId, startingDataWord+i, words[i]);
        }
        initData.setWords(blockId, startingDataWord, words);
        Map<String,Object> fmap = dfd.decode(blockId, startingDataWord, words);
        for(Entry<String,Object> e : fmap.entrySet()) {
            System.out.println(e.getKey()+" = "+e.getValue().toString());
        }
       
    }
    public void processTIM03(NATIM03 tim03) {
/*         JWordData jwd = new JWordData();
         for(int i=0;i<70;i++) {
             System.out.println("XX:"+i+" => "+jwd.getWordIndex(i)+","+jwd.getBitIndex(i));
         }
*/
         Link16WordData[] l16data = JDataConverter.getLink16WordData(tim03.getData());
         Link16Word[] awords = JDataConverter.toAOCSLink16Words(l16data);
         Header hdr = new Header(awords.length*12, DataElementType.LINK16.ordinal(), tim03.getSTN(), MulticastClass.RAP.ordinal());         
         hdr.setTime(SystemClock.getInstance().now().toEpochMilli());
         Link16 l16de = new Link16(hdr, awords);
         
         AOCSModule.getInstance().transmit(l16de);
         AOCSModule.getInstance().write(l16de);
         
         for(Message m : JDataConverter.decode(l16data)) {
             System.out.print(Instant.ofEpochMilli(l16de.getHeader().getTime())+":JSERIES:");
             System.out.print("J"+m.getLabel()+"."+m.getSublabel());
             if((m.getLabel().getValue()==3) && (m.getSublabel().getValue()==2)) {               
                 System.out.print(" ,TN="+((J3_2)m).get_J3_2_I_Word().trackNumber.get().toString());
                 System.out.print(" ,COURSE="+((J3_2)m).get_J3_2_E0_Word().fieldCourse.toString());
                 System.out.print(" ,SPEED="+((J3_2)m).get_J3_2_E0_Word().fieldSpeed.toString());
             }
             System.out.println();
         }
         
         byte[] data = CoderTest.encode(l16de);
         NATOM03 tom03 = CoderTest.toTOM03(l16de, 0, tim03.getTime());
         JTIDSDataFrame[] ftom03=tom03.encode();
         
         int y=10;
    }
    
    public void processTIM01(NATIM01 tim01) {
        for(DataBlock db : tim01.getDatablocks()) {
            if(db.getControlWord().isInitData()) {
                System.out.print("SET_INIT_DATA: blockId="+db.getDataWordControlWord().getBlockId()+" ,startingWordId="+db.getDataWordControlWord().getStartingDataWord());
                System.out.print(" ,data=");
                for(int i=0;i<db.getDataWords().length;i++) {
                    System.out.print(String.format("%04x,", db.getDataWords()[i]));
                }
                System.out.println();
                onInitDataChange(db.getDataWordControlWord().getBlockId(), db.getDataWordControlWord().getStartingDataWord(),db.getDataWords());
                System.out.println("-------------------------------------");
                
            }else{
                int y=10;
            }
        }
    }
    public void processTIM(NATxM tim) {
        if(tim instanceof NATIM01) {
            processTIM01((NATIM01)tim);
        }else if(tim instanceof NATIM03) {
//            processTIM03((NATIM03)tim);
        }
    }
    @Override
    public void run() {
        NATIMReader tr = new NATIMReader(bimSource);
        while (true) {
            NATxM tim;
            try {
                tim = tr.read();
                if (tim == null) {
                    break;
                }                
            } catch (IOException ex) {
                break;
            }
            processTIM(tim);
        }
    }

}
