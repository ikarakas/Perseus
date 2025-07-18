/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.data.DataFieldDecoder;
import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01;
import fxmlib.fxm.FIM;
import fxmlib.fxm.FIM03;
import fxmlib.fxm.FIM03_InitDataChange;
import java.io.IOException;
import java.math.BigInteger;
import java.util.BitSet;
import java.util.Collection;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 *
 * @author mike
 */
public class InitDataChangeMapper {
    protected final JTIDSInitData jtidsInitData;
    protected final MIDSInitData midsInitData;

    protected final static DataFieldDecoder dfdJTIDS = new DataFieldDecoder(DataFieldDefinition.DataDomain.JTIDS_INITIALIZATION);
    protected final static DataFieldDecoder dfdMIDS = new DataFieldDecoder(DataFieldDefinition.DataDomain.MIDS_INITIALIZATION);
    
    public InitDataChangeMapper(JTIDSInitData jtidsInitData, MIDSInitData midsInitData) {
        this.jtidsInitData=jtidsInitData;
        this.midsInitData=midsInitData;
    }
    protected int getCode(Object obj) {
        if(obj instanceof BigInteger) {
            return  ((BigInteger)obj).intValue();
        }
        throw new IllegalArgumentException();
    }
    public void read(String fileName) throws IOException  {           
        jtidsInitData.data.read(fileName);
    }
    public List<FIM> translate(Collection<NATIM01.DataBlock> dataBlocks) {
        LinkedList<FIM> fim03List = new LinkedList<>();
        for(NATIM01.DataBlock db : dataBlocks) {
            fim03List.addAll(toFIM03(db.getInitializationBlockId(), db.getStartingDataWord(), db.getDataWords()));
        }
        return fim03List;
    }
    protected List<FIM03> toFIM03(int blockId, int startingWordId, int[] words) {
        jtidsInitData.setWords(blockId, startingWordId, words);
        Map<String,Object> fmap = dfdJTIDS.decode(blockId, startingWordId, words);
        Map<DataFieldDefinition, Integer> midsFieldCodeMap=new TreeMap<>();
        
        for(Map.Entry<String,Object> e : fmap.entrySet()) {
            DataFieldDefinition mdfd = dfdMIDS.getFieldDefinitions().get(e.getKey());
            if(mdfd==null) {
                continue;
            }
            midsFieldCodeMap.put(mdfd, getCode(e.getValue()));
        }  
        
        int y=10;
        BitSet midsWordChangeSet = new BitSet();
        for(Map.Entry<DataFieldDefinition, Integer> e : midsFieldCodeMap.entrySet()) {
            for(int i=0;i<midsInitData.wordCount(e.getKey());i++) {
                midsWordChangeSet.set(e.getKey().getWordId()+i);                
            }
            midsInitData.setField(e.getKey(), e.getValue());
        }
        LinkedList<FIM03> fim03List = new LinkedList<>();
        
            
        int startWord=0;
        while(true) {
            startWord = midsWordChangeSet.nextSetBit(startWord);
            if(startWord<0) {
                break;
            }
            int endWord = midsWordChangeSet.nextClearBit(startWord);
            int wordCount=endWord-startWord;
            if(wordCount>30) {
                endWord=startWord+30;
                wordCount=30;
            }
            int[] data = new int[wordCount];
            for(int i=0;i<data.length;i++) {
                data[i]=midsInitData.getWordData().getWord(0, startWord+i);
            }
            FIM03_InitDataChange fim=new FIM03_InitDataChange(0, startWord, data);
            fim03List.add(fim);
            startWord=endWord;
        }
        return fim03List;
    }
    public void updateInitDataFromMIDS(int startDataWord, int[] words) {
        midsInitData.getWordData().setWords(0, startDataWord, words);
        Map<String,Object> fieldMap = dfdMIDS.decode(0, startDataWord, words);        
        for(Map.Entry<String,Object> e : fieldMap.entrySet()) {
            DataFieldDefinition jdfd = dfdJTIDS.getFieldDefinitions().get(e.getKey());
            if(jdfd==null) {
                continue;
            }
            int code=getCode(e.getValue());
//            System.out.println("#JTIDS_INIT_DATA.SET("+jdfd.getName()+"):="+code);
            jtidsInitData.fieldView.setCode(jdfd, code);
        }          

    }
}
