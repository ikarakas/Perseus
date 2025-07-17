/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tom1;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldType;
import java.util.Arrays;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class NATOM01 implements NATxM {
    protected final List<Field> fields;
    protected LinkedList<DataBlock> datablocks;
    
    public NATOM01(LinkedList<DataBlock> datablocks) {
        this.datablocks=datablocks;
        this.fields=Collections.EMPTY_LIST;
    }

    public NATOM01(List<Field> fields) {
        this.fields = fields;
    }

    @Override
    public boolean isTIM() {
        return false;
    }

    @Override
    public int getBlockId() {
        return 1;
    }

    public LinkedList<DataBlock> getDatablocks() {
        return datablocks;
    }
    
    @Override
    public Iterable<Field> fields() {
        return fields;
    }

    @Override
    public String getName() {
        return "TOM1";
    }
    protected static NATOM01 decode(int[] halfwords) {
        int idx = 0;
        LinkedList<DataBlock> datablocks = new LinkedList<>();
        
        while (idx<halfwords.length) {
            if (halfwords[idx] == 0) {
                break;
            }
            ControlWord cw = ControlWord.TYPE.decode(halfwords[idx++]);
            
            DataWordControlWord dwcw = DataWordControlWord.TYPE.decode(halfwords[idx++]);
            int[] datawords = new int[dwcw.dataWordCount];
            for(int i=0;i<datawords.length;i++) {
                datawords[i]=halfwords[idx++];
            }
            DataBlock db = new DataBlock(cw, dwcw, datawords);
            datablocks.add(db);
        }
        return new NATOM01(datablocks);
    }
    protected static NATOM01 generateTOM01(DataBlock db) {
        LinkedList<DataBlock> datablocks = new LinkedList<>();
        datablocks.add(db);
        return new NATOM01(datablocks);
    }
    @Override
    public JTIDSDataFrame[] encode() {
        int numHalfWords=0;
        int idx=0;
        int[] hw=new int[32];
        
        for(DataBlock db : datablocks) {
            int[] dbhw = db.asHalfWords();
            numHalfWords+=dbhw.length;
            for(int i=0;i<dbhw.length;i++,idx++) {
                hw[idx]=dbhw[i];
            }
        }
        
        if(numHalfWords<=16) {
            NABOM01 bom0=new NABOM01(1, false, Arrays.copyOfRange(hw, 0, numHalfWords));
            return bom0.encode();
        }else{
            NABOM01 bom0=new NABOM01(1, true, Arrays.copyOfRange(hw, 0, 16));            
            NABOM01 bom1=new NABOM01(2, false, Arrays.copyOfRange(hw, 16, 32));    
            JTIDSDataFrame[] frames=new JTIDSDataFrame[2];
            frames[0]=bom0.encode()[0];
            frames[1]=bom1.encode()[0];
            return frames;
        }
    }

    public static NATOM01 generateTOM01_StatusDataResponse(int blockId, int  startWordId, int[] data) {
        DataBlock db = createStatusDataResponse(blockId, startWordId, data);
        return generateTOM01(db);
    }
    public static NATOM01 generateTOM01_InitDataResponse(int blockId, int  startWordId, int[] data) {
        DataBlock db = createInitDataResponse(blockId, startWordId, data);
        return generateTOM01(db);
    }
    public static NATOM01 decode(NABOM01 bom) {
        int[] words=new int[16];
        for(int i=0;i<16;i++) {
            words[i]=bom.halfwords[i];
        }
        return decode(words);
    }
    public static NATOM01 decode(NABOM01 bom0, NABOM01 bom1) {
        int[] words=new int[32];
        for(int i=0;i<16;i++) {
            words[i]=bom0.halfwords[i];
        }
        for(int i=16;i<32;i++) {
            words[i]=bom1.halfwords[i-16];
        }
        return decode(words);
    }
    public static DataBlock createStatusDataResponse(int blockId, int startingWordId, int[] halfwords) {
        ControlWord cw = new ControlWord(2, 0, 0, 2, 0);
        DataWordControlWord dwcw = new DataWordControlWord(blockId, startingWordId, halfwords.length);
        return new DataBlock(cw, dwcw, halfwords);
    }
    public static DataBlock createInitDataResponse(int blockId, int startingWordId, int[] halfwords) {
        ControlWord cw = new ControlWord(2, 0, 0, 3, 0);
        DataWordControlWord dwcw = new DataWordControlWord(blockId, startingWordId, halfwords.length);
        return new DataBlock(cw, dwcw, halfwords);        
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
        public int getBlockId() {
            return dataWordControlWord.blockId;
        }
        public int getStartingDataWord() {
            return dataWordControlWord.startingDataWord;
        }

        public ControlWord getControlWord() {
            return controlWord;
        }

        public int[] getDataWords() {
            return dataWords;
        }
        public boolean isStatusData() {
            return controlWord.isStatusData();
        }
        public boolean isInitData() {
            return controlWord.isInitData();
        }
        
        @Override
        public String toString() {
            StringBuilder sb = new StringBuilder();
            sb.append("{initializationBlockId=");
            sb.append(getBlockId());
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
        public int[] asHalfWords() {
            int[] hw = new int[2+dataWordControlWord.dataWordCount];
            hw[0]=(int)(ControlWord.TYPE.encode(controlWord) & 0xffff);
            hw[1]=(int)(DataWordControlWord.TYPE.encode(dataWordControlWord) & 0xffff);
            for(int i=0;i<dataWords.length;i++) {
                hw[2+i]=dataWords[i];
            }
            return hw;
        }
    }
    public static class ControlWord {

        int addressTypeSpecifier; //1=physical, 2=datawordcode
        int addressExtension;
        int addressLocator;
        int responseType; // 1=physical,2=status, 3=initdata
        int wordCount;

        public ControlWord(int addressTypeSpecifier, int addressExtension, int addressLocator, int responseType, int wordCount) {
            this.addressTypeSpecifier = addressTypeSpecifier;
            this.addressExtension = addressExtension;
            this.addressLocator = addressLocator;
            this.responseType = responseType;
            this.wordCount = wordCount;
        }
        public boolean isStatusData() {
            return (addressTypeSpecifier==2) && (responseType==2);
        }
        public boolean isInitData() {
            return (addressTypeSpecifier==2) && (responseType==3);
        }
        public boolean isDataWord() {
            return addressTypeSpecifier==2;
        }
        @Override
        public String toString() {
            return "{" + ", addressTypeSpecifier=" + addressTypeSpecifier + ", addressExtension=" + addressExtension + ", addressLocator=" + addressLocator + ", responseType=" + responseType + ", wordCount=" + wordCount + '}';
        }

        public int getResponseTypeCode() {
            return responseType;
        }
        
        public static final FieldType<ControlWord> TYPE = new FieldType<>() {
            @Override
            public int getLength() {
                return 16;
            }

            @Override
            public ControlWord decode(long code) {
                int wordCount = (int) (code & 0x1f);
                int responseType = (int) ((code >> 5) & 0x3);
                int addressLocator = (int) ((code >> 7) & 0x1);
                int addressExtension = (int) ((code >> 8) & 0xf);
                int addressTypeSpecifier = (int) ((code >> 12) & 0x3);
                int blockType = (int) ((code >> 14) & 0x3);
                return new ControlWord(addressTypeSpecifier, addressExtension, addressLocator, responseType, wordCount);
            }

            @Override
            public long encode(ControlWord value) {
                long code=(value.wordCount&0x1f)|(value.responseType<<5)|(value.addressLocator<<7)|(value.addressExtension<<8)|(value.addressTypeSpecifier<<12);
                return code;
            }

        };
    }

    public static class DataWordControlWord {

        int blockId;
        int startingDataWord;
        int dataWordCount;

        public DataWordControlWord(int blockId, int startingDataWord, int dataWordCount) {
            this.blockId = blockId;
            this.startingDataWord = startingDataWord;
            this.dataWordCount = dataWordCount;
        }

        public static final FieldType<DataWordControlWord> TYPE = new FieldType<>() {
            @Override
            public int getLength() {
                return 16;
            }

            @Override
            public DataWordControlWord decode(long code) {
                int dataWordCount = (int) (code & 0x1f);
                int startingDataWord = (int) ((code >> 5) & 0x1f);
                int initializationBlockId = (int) ((code >> 10) & 0x3f);
                return new DataWordControlWord(initializationBlockId, startingDataWord, dataWordCount);
            }

            @Override
            public long encode(DataWordControlWord value) {
                long code=(value.dataWordCount&0x1f)|(value.startingDataWord<<5)|(value.blockId<<10);
                return code;
            }

        };
    }

    public static class AddressControlWord {

        int address;

        public AddressControlWord(int address) {
            this.address = address;
        }

        public static final FieldType<AddressControlWord> TYPE = new FieldType<>() {
            @Override
            public int getLength() {
                return 16;
            }

            @Override
            public AddressControlWord decode(long code) {
                int address = (int) (code & 0xffff);
                return new AddressControlWord(address);
            }

            @Override
            public long encode(AddressControlWord value) {
                throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
            }

        };
    }

}
