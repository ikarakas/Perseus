/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.data.DataFieldView;
import _int.nato.ncia.natxmlib.data.WordDataStore;
import java.math.BigInteger;
import java.util.Map;
import java.util.TreeMap;

/**
 *
 * @author mike
 */
public class JTIDSStatusData {

    protected final WordDataStore data = new WordDataStore();
    protected final DataFieldView fieldView = new DataFieldView(DataFieldDefinition.DataDomain.JTIDS_STATUS, data);

    public JTIDSStatusData() {
    }

    public void setWord(int blockId, int wordId, int value) {
        data.setWord(blockId, wordId, value);
//        System.out.println("SET_STATUS_DATA(" + blockId + "," + wordId + ")=" + String.format("0x%04x", value));
    }

    public int getWord(int blockId, int wordId) {
        return data.getWord(blockId, wordId);
    }

    public void setWords(int blockId, int startingWordId, int[] words) {
        for (int i = 0; i < words.length; i++) {
            setWord(blockId, startingWordId + i, words[i]);
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
        TreeMap<String, Long> vmap = new TreeMap<>();
        for (String fieldName : fieldView.fieldNames()) {
            BigInteger bi = fieldView.getBigCode(fieldName);
            vmap.put(fieldName, bi.longValue());
        }
        return vmap;
    }
}
