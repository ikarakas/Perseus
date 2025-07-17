/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.data.DataFieldView;
import _int.nato.ncia.natxmlib.data.WordDataStore;
import _int.nato.ncia.natxmlib.types.TwosComplement;
import java.math.BigInteger;
import java.util.Map;
import java.util.TreeMap;

/**
 *
 * @author mike
 */
public class JTIDSInitData {
    protected final WordDataStore data = new WordDataStore();
    protected final DataFieldView fieldView = new DataFieldView(DataFieldDefinition.DataDomain.JTIDS_INITIALIZATION, data);

    public JTIDSInitData() {
    }
    
    public int getTerminalAddress() {
        return fieldView.getBigCode("TERMINAL ADDRESS").intValue();
    }

    public void setWord(int blockId, int wordId, int value) {
        data.setWord(blockId, wordId, value);
//        System.out.println("SET_INIT_DATA("+blockId+","+wordId+")="+String.format("0x%04x",value));
    }
    public int getWord(int blockId, int wordId) {
        return data.getWord(blockId, wordId);
    }
    public void setWords(int blockId, int startingWordId, int[] words) {
        for(int i=0;i<words.length;i++) {
            setWord(blockId, startingWordId+i, words[i]);
        }
    }
    public int[] getWords(int blockId, int startingWordId, int count) {
        int[] words = new int[count];
        for(int i=0;i<count;i++) {
            words[i]=getWord(blockId,startingWordId+i);
        }
        return words;
    }
    public Map<String, Long> getFieldCodes() {
        TreeMap<String,Long> vmap = new TreeMap<>();
        for(String fieldName : fieldView.fieldNames()) {
            BigInteger bi = fieldView.getBigCode(fieldName);
            vmap.put(fieldName, bi.longValue());
        }
        return vmap;
    }
    public double getCCCSLatitude() {
        int iw5=getWord(56, 5);
        int iw6=getWord(56, 6);
        boolean originChange = ((iw5 >> 31 )&0x1)==1;
        boolean earthModelWGS84 = ((iw5 >> 30 )&0x1)==1;
        int code=((iw5&0xf)<<16)|(iw6 & 0xffff);
        double fact= 360.0/(1<<20);
        return new TwosComplement(20,fact, code).getValue();
    }
    public double getCCCSLongitude() {
        int iw7=getWord(56, 7);
        int iw8=getWord(56, 8);
        int code=((iw7&0xf)<<16)|(iw8 & 0xffff);
        double fact= 360.0/(1<<20);
        return new TwosComplement(20,fact, code).getValue();
    }
    public static double STD_EARTH_RADIUS_NM=3_440.0647948;
    
    public double getCCCSEarthRadius() {        
        int iw9=getWord(56, 9);
        int iw10=getWord(56, 10);        
        int code=((iw9&0x3f)<<16)|(iw10 & 0xffff);
        double fact=4194.304/(1<<22);
        return code*fact;
    }
}
