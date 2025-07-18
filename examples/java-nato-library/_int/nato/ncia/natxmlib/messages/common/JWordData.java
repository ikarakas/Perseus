package _int.nato.ncia.natxmlib.messages.common;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;

/**
 *
 * @author mike
 */
public class JWordData extends SubgroupData {
    
    protected int[] jdwords; 
    protected int[] fwords;
    
    // 15..0
    //31..16
    //47..32
    //53..48
    //69..54
    public JWordData() {
        super(0);
        jdwords=new int[5];
    }

    public JWordData(JTIDSDataFrame f, int wordOffset) {
        super(0);
        fwords=new int[]{
            f.getWord(wordOffset),
            f.getWord(wordOffset+1),
            f.getWord(wordOffset+2)
        };
        jdwords = new int[]{
        f.getCode(wordOffset, 16, 16), //
        f.getCode(wordOffset + 1, 0, 16), 
        f.getCode(wordOffset + 1, 16, 16), 
        f.getCode(wordOffset + 2, 0, 16), 
        f.getCode(wordOffset + 2, 16, 16)};
    } //
    @Override
    public void put(JTIDSDataFrame f, int wordOffset) {
        f.setWord(wordOffset, jdwords[0]<<16);
        f.setWord(wordOffset+1, (jdwords[2]<<16)|jdwords[1]);
        f.setWord(wordOffset+2, (jdwords[4]<<16)|jdwords[3]);
    }
    public int getWordIndex(int jBitIndex) {
        if ((jBitIndex >= 0) && (jBitIndex <= 15)) {
            return 0;
        } else if ((jBitIndex >= 16) && (jBitIndex <= 31)) {
            return 1;
        } else if ((jBitIndex >= 32) && (jBitIndex <= 47)) {
            return 2;
        } else if ((jBitIndex >= 48) && (jBitIndex <= 53)) {
            return 3;
        } else if ((jBitIndex >= 54) && (jBitIndex <= 69)) {
            return 4;
        } else {
            throw new IllegalArgumentException();
        }
    }
    public int getBitIndex(int jBitIndex) {
        if (jBitIndex >= 48) {
            return (jBitIndex+10)%16;
        } else {
            return jBitIndex%16;
        }
    }
    public boolean isBitSet(int jBitIndex) {
        return (jdwords[getWordIndex(jBitIndex)] & (1 << getBitIndex(jBitIndex))) != 0;        
    }

    public void setBit(int jBitIndex, boolean state) {
        if (state) {
            jdwords[getWordIndex(jBitIndex)] |= (1 << getBitIndex(jBitIndex));
        } else {
            jdwords[getWordIndex(jBitIndex)] &= ~(1 << getBitIndex(jBitIndex));
        }
    }
    public int getHalfword(int idx) {
        return jdwords[idx];
    }

    @Override
    public String toString() {
        return String.format("%04X %04X %04X %04X %04X",jdwords[0],jdwords[1],jdwords[2],jdwords[3],jdwords[4]);
    }
    
}
