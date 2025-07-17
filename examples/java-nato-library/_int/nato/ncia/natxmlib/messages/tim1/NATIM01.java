package _int.nato.ncia.natxmlib.messages.tim1;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.messages.NATIM;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldType;
import java.util.Collections;
import java.util.LinkedList;

/**
 *
 * @author mike
 */
public class NATIM01 extends NATIM {
    protected LinkedList<DataBlock> datablocks;
    protected NABIM01[] bims;
    
    public NATIM01(LinkedList<DataBlock> datablocks) {
        this.datablocks=datablocks;
    }
    public static NATIM01 create(LinkedList<DataBlock> datablocks) {
        int[] halfwords = new int[32];
        int idx=0;
        for(DataBlock db : datablocks) {
            int[] dbhw = db.toHalfwords();
            for(int i=0;i<dbhw.length;i++,idx++) {
                halfwords[idx]=dbhw[i];
            }
        }
        if(idx<16) {
            NABIM01 bim0=NABIM01.create(false, 1, halfwords);
            NATIM01 tim = new NATIM01(new LinkedList<>(datablocks));
            tim.bims=new NABIM01[]{bim0};
            return tim;
        }else{
            NABIM01 bim0=NABIM01.create(true, 1, halfwords);
            NABIM01 bim1=NABIM01.create(false, 2, halfwords);
            NATIM01 tim = new NATIM01(new LinkedList<>(datablocks));
            tim.bims=new NABIM01[]{bim0,bim1};            
            return tim;
        }
    }
    @Override
    public JTIDSDataFrame[] encode() {
        LinkedList<JTIDSDataFrame> bimList=new LinkedList<>();
        for(NABIM01 bim : bims) {
            bimList.add(bim.encode()[0]);
        }
        return bimList.toArray(new JTIDSDataFrame[0]);
    }
    
    protected static NATIM01 decode(int[] halfwords) {
        int idx = 0;
        LinkedList<DataBlock> datablocks = new LinkedList<>();
        
        while (idx<halfwords.length) {
            if (halfwords[idx] == 0) {
                break;
            }
            ControlWord cw = ControlWord.TYPE.decode(halfwords[idx++]);
            if(!cw.isInitData()) {
                break;
            }
            if(idx>=halfwords.length) {
                break;
            }
            DataWordControlWord dwcw = DataWordControlWord.TYPE.decode(halfwords[idx++]);
            int[] datawords = new int[dwcw.dataWordCount];
            for(int i=0;i<datawords.length;i++) {
                datawords[i]=halfwords[idx++];
            }
            DataBlock db = new DataBlock(cw, dwcw, datawords);
            datablocks.add(db);
        }
        return new NATIM01(datablocks);
    }
    public static NATIM01 decode(NABIM01 bim) {
        int[] words=new int[16];
        for(int i=0;i<16;i++) {
            words[i]=bim.halfwords[i];
        }
        NATIM01 tim= decode(words);
        tim.bims=new NABIM01[]{bim};
        return tim;
    }
    public static NATIM01 decode(NABIM01 bim0, NABIM01 bim1) {
        int[] words=new int[32];
        for(int i=0;i<16;i++) {
            words[i]=bim0.halfwords[i];
        }
        for(int i=16;i<32;i++) {
            words[i]=bim1.halfwords[i-16];
        }
        NATIM01 tim= decode(words);
        tim.bims=new NABIM01[]{bim0,bim1};
        return tim;
    }
    public boolean isInitDataChange() {
        return ((Field<Boolean>)(bims[0].getField("INITIALIZATION BLOCK TYPE"))).getValue();
        
    }
    public boolean hasNewCCSOrigin() {
        return ((Field<Boolean>)(bims[0].getField("NEW CCCS ORIGIN"))).getValue();        
    }
    public LinkedList<DataBlock> getDatablocks() {
        return datablocks;
    }
    
    @Override
    public int getBlockId() {
        return 1;
    }

    @Override
    public Iterable<Field> fields() {
        return Collections.EMPTY_LIST;
    }
    public static DataBlock buildInitDataChange(int blkId, int wordId, int[] data) {
        ControlWord cw = new ControlWord(2, 2, 0,0,3,0);
        DataWordControlWord dwcw = new DataWordControlWord(blkId, wordId, data.length);
        return new DataBlock(cw, dwcw, data);
    }
    public static class DataBlock {
        protected ControlWord controlWord;
        protected DataWordControlWord dataWordControlWord;
        protected int[] dataWords;

        public DataBlock(ControlWord controlWord, DataWordControlWord dataWordControlWord, int[] dataWords) {
            this.controlWord = controlWord;
            this.dataWordControlWord = dataWordControlWord;
            this.dataWords = dataWords;
        }
        public int getInitializationBlockId() {
            return dataWordControlWord.initializationBlockId;
        }
        public int getStartingDataWord() {
            return dataWordControlWord.startingDataWord;
        }

        public int[] getDataWords() {
            return dataWords;
        }

        public ControlWord getControlWord() {
            return controlWord;
        }

        public DataWordControlWord getDataWordControlWord() {
            return dataWordControlWord;
        }
        
        @Override
        public String toString() {
            StringBuilder sb = new StringBuilder();
            sb.append("{initializationBlockId=");
            sb.append(getInitializationBlockId());
            sb.append(", startingDataWord=");
            sb.append(getStartingDataWord());
            sb.append(", words=");
            for(int i=0;i<dataWords.length;i++) {
                sb.append(String.format("0x%04x", dataWords[i]));
                if(i<dataWords.length-1) {
                    sb.append(", ");
                }
            }
            sb.append("}");
            return sb.toString();
        }
        public int[] toHalfwords() {
            int[] result=new int[2+dataWords.length];
            result[0]=(int)ControlWord.TYPE.encode(controlWord);
            result[1]=(int)DataWordControlWord.TYPE.encode(dataWordControlWord);
            for(int i=0;i<dataWords.length;i++) {
                result[2+i]=dataWords[i];
            }
            return result;
        }
    }
    public static class ControlWord {
        int blockType;
        int addressTypeSpecifier;
        int addressExtension;
        int addressLocator;
        int requestType;
        int wordCount;

        public ControlWord(int blockType, int addressTypeSpecifier, int addressExtension, int addressLocator, int requestType, int wordCount) {
            this.blockType = blockType;
            this.addressTypeSpecifier = addressTypeSpecifier;
            this.addressExtension=addressExtension;
            this.addressLocator = addressLocator;
            this.requestType = requestType;
            this.wordCount = wordCount;
        }

        @Override
        public String toString() {
            return "{" + "blockType=" + blockType + ", addressTypeSpecifier=" + addressTypeSpecifier + ", addressExtension=" + addressExtension + ", addressLocator=" + addressLocator + ", requestType=" + requestType + ", wordCount=" + wordCount + '}';
        }
        
        public static final FieldType<ControlWord> TYPE = new FieldType<>() {
            @Override
            public int getLength() {
                return 16;
            }

            @Override
            public ControlWord decode(long code) {
                int wordCount=(int)(code & 0x1f);
                int requestType=(int)((code >> 5) & 0x3);
                int addressLocator = (int)((code >> 7) & 0x1);
                int addressExtension = (int)((code >> 8) & 0xf);
                int addressTypeSpecifier = (int)((code >> 12) & 0x3);
                int blockType = (int)((code >> 14) & 0x3);
                return new ControlWord(blockType, addressTypeSpecifier,addressExtension, addressLocator,requestType,wordCount);
            }

            @Override
            public long encode(ControlWord value) {
                long code=0;
                code|=(value.wordCount & 0x1f);
                code|=((value.requestType & 0x3)<<5);
                code|=((value.addressLocator & 0x1)<<7);
                code|=((value.addressExtension & 0xf)<<8);
                code|=((value.addressTypeSpecifier & 0x3)<<12);
                code|=((value.blockType & 0x3)<<14);
                return code;                
            }
            
        };
        public boolean isInitData() {
            return requestType==3;
        }
    }
    public static class DataWordControlWord {
        int initializationBlockId;
        int startingDataWord;
        int dataWordCount;

        public DataWordControlWord(int initializationBlockId, int startingDataWord, int dataWordCount) {
            this.initializationBlockId = initializationBlockId;
            this.startingDataWord = startingDataWord;
            this.dataWordCount = dataWordCount;
        }

        public int getBlockId() {
            return initializationBlockId;
        }

        public int getStartingDataWord() {
            return startingDataWord;
        }

        public int getDataWordCount() {
            return dataWordCount;
        }
        
        public static final FieldType<DataWordControlWord> TYPE = new FieldType<>() {
            @Override
            public int getLength() {
                return 16;
            }

            @Override
            public DataWordControlWord decode(long code) {
                int dataWordCount=(int)(code & 0x1f);
                int startingDataWord=(int)((code >> 5) & 0x1f);
                int initializationBlockId = (int)((code >> 10) & 0x3f);
                return new DataWordControlWord(initializationBlockId,startingDataWord,dataWordCount);
            }

            @Override
            public long encode(DataWordControlWord value) {
                long code=0;
                code|=(value.dataWordCount & 0x1f);
                code|=((value.startingDataWord & 0x1f)<<5);
                code|=((value.initializationBlockId & 0x3f)<<10);
                return code;
            }
            
        };
    }
    
}
