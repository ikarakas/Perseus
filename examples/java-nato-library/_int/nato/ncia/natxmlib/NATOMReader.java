package _int.nato.ncia.natxmlib;


import _int.nato.ncia.natxmlib.messages.NATOM_WRAP_AROUND;
import _int.nato.ncia.natxmlib.messages.NATIM_Unknown;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tom1.NABOM01;
import _int.nato.ncia.natxmlib.messages.tom1.NATOM01;
import _int.nato.ncia.natxmlib.messages.tom1.NATOM01.DataBlock;
import _int.nato.ncia.natxmlib.messages.tom3.NABOM03;
import _int.nato.ncia.natxmlib.messages.tom3.NATOM03;
import _int.nato.ncia.natxmlib.messages.tom4.NATOM04;
import _int.nato.ncia.natxmlib.messages.tom6.NATOM06;
import java.io.IOException;
import java.util.LinkedList;

/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */

/**
 *
 * @author mike
 */
public class NATOMReader {
    protected final JTIDSDataFrameSource source;

    public NATOMReader(JTIDSDataFrameSource source) {
        this.source = source;
    }
    protected JTIDSDataFrame readNextFrame() throws IOException {
        return source.read();
    }
    public void testTOM01(NATOM01 tom01,JTIDSDataFrame frame0, JTIDSDataFrame frame1) {
        LinkedList<DataBlock> dblist=new LinkedList<>();
        
        for(DataBlock db : tom01.getDatablocks()) {
            if(db.getControlWord().getResponseTypeCode()==2) {
                int[] data = db.getDataWords();
                int startWord=db.getStartingDataWord();
                int startBlk=db.getBlockId();
                DataBlock db_new = NATOM01.createStatusDataResponse(startBlk, startWord, data);                
                dblist.add(db_new);
            }else if(db.getControlWord().getResponseTypeCode()==3) {
                int[] data = db.getDataWords();
                int startWord=db.getStartingDataWord();
                int startBlk=db.getBlockId();
                DataBlock db_new = NATOM01.createInitDataResponse(startBlk, startWord, data);                
                dblist.add(db_new);
            } else {
                throw new IllegalArgumentException();
            }
        }
        NATOM01 tom_new = new NATOM01(dblist);
        JTIDSDataFrame[] df_new = tom_new.encode();
        if (df_new.length != 2) {
          throw new IllegalArgumentException();          
        }
        JTIDSDataFrame frame_0_new = df_new[0];
        JTIDSDataFrame frame_1_new = df_new[1];
        for (int i = 0; i < 9; i++) {
            if (frame0.getWord(i) != frame_0_new.getWord(i)) {
                throw new IllegalArgumentException();
            }
        }
        for (int i = 0; i < 9; i++) {
            if (frame1.getWord(i) != frame_1_new.getWord(i)) {
                throw new IllegalArgumentException();
            }
        }
        System.out.println("TOM 1 OK");
    }
    public void testTOM01(NATOM01 tom01,JTIDSDataFrame frame0) {
     LinkedList<DataBlock> dblist=new LinkedList<>();
        
        for(DataBlock db : tom01.getDatablocks()) {
            if(db.getControlWord().getResponseTypeCode()==2) {
                int[] data = db.getDataWords();
                int startWord=db.getStartingDataWord();
                int startBlk=db.getBlockId();
                DataBlock db_new = NATOM01.createStatusDataResponse(startBlk, startWord, data);                
                dblist.add(db_new);
            }else if(db.getControlWord().getResponseTypeCode()==3) {
                int[] data = db.getDataWords();
                int startWord=db.getStartingDataWord();
                int startBlk=db.getBlockId();
                DataBlock db_new = NATOM01.createInitDataResponse(startBlk, startWord, data);                
                dblist.add(db_new);
            } else {
                throw new IllegalArgumentException();
            }
        }        
        NATOM01 tom_new = new NATOM01(dblist);
        JTIDSDataFrame[] df_new = tom_new.encode();
        if (df_new.length != 1) {
          throw new IllegalArgumentException();          
        }
        JTIDSDataFrame frame_0_new = df_new[0];
        for (int i = 0; i < 9; i++) {
            if (frame0.getWord(i) != frame_0_new.getWord(i)) {
                throw new IllegalArgumentException();
            }
        }
        System.out.println("TOM 1 OK - short one");
    }

    public NATxM decodeTOM1(JTIDSDataFrame frame0) throws IOException {
        NABOM01 bom0=NABOM01.decode(frame0);
        if(bom0.getSubBlockId()!=1) {
            throw new IllegalArgumentException();
        }
        if(!bom0.isBFI()) {
            NATOM01 tom01 = NATOM01.decode(bom0);
//            testTOM01(tom01, frame0);
            return tom01;
        }else{
            JTIDSDataFrame frame1=readNextFrame();
            NABOM01 bom1=NABOM01.decode(frame1);            
            if(bom1.getSubBlockId()!=2) {
                throw new IllegalArgumentException();
            }
            
            NATOM01 tom01 = NATOM01.decode(bom0, bom1);
//            testTOM01(tom01,frame0,frame1);
            return tom01;
        }
    }
    public NATxM decodeTOM3(JTIDSDataFrame frame0) throws IOException {
        NABOM03 bom0=NABOM03.decode(frame0);
        if(bom0.getSubBlockId()!=1) {
            throw new IllegalArgumentException();
        }
        LinkedList<NABOM03> bomList = new LinkedList<>();
        bomList.add(bom0);
        for(int i=2;(i<7) && (i<=bom0.getSubBlockCount());i++) {
            NABOM03 bimx=NABOM03.decode(readNextFrame());
            if(bimx.getSubBlockId()!=i) {
                throw new IllegalArgumentException();
            }
            bomList.add(bimx);
        }
        return NATOM03.decode(bomList.toArray(new NABOM03[0]));
        
    }
    public NATxM read() throws IOException {
        JTIDSDataFrame frame = readNextFrame();
        if(frame==null) {
            return null;
        }
        int wi = frame.getCode(0, 0, 1);
        if(wi==1) {
            NATxM txm = NATOM_WRAP_AROUND.decode(frame);
            return txm;
        }
        int blkId = frame.getCode(0, 1, 5);
        switch(blkId) {
            case 1:
                return decodeTOM1(frame);
            case 3:
                return decodeTOM3(frame);
            case 2:
                return NATIM_Unknown.decode(frame);
            case 4:                
                return NATOM04.decode(frame);
            case 5:
                return NATIM_Unknown.decode(frame);
            case 6:
                return NATOM06.decode(frame);
        }
        return NATIM_Unknown.decode(frame);
    }
    public void close() {
        source.close();
    }
}
