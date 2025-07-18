/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.DumpFile;
import _int.nato.ncia.natxmlib.NATIMReader;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.data.DataFieldDictionary;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tim1.NATIM01;
import fxmlib.fxm.FIM;
import java.io.IOException;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class InitDataTest {
    public static void test_1(InitDataChangeMapper mapper) {
    }
    public static void test_2(InitDataChangeMapper mapper) throws IOException {
        LinkedList<DumpFile.Record> bimList = new LinkedList<>();

        for (DumpFile.Record r : DumpFile.parse("dump2.txt")) {
            if (r.isTIM()) {
                bimList.add(r);
            }
        }
        TextDumpDecoder.FrameSource bimSource = new TextDumpDecoder.FrameSource(bimList);
        NATIMReader tr = new NATIMReader(bimSource);
        while (true) {
            NATxM tim;
            try {
                tim = tr.read();
                if (tim == null) {
                    break;
                }
                if(tim instanceof NATIM01) {
                    List<FIM> fim03List=mapper.translate(((NATIM01) tim).getDatablocks());
                    if(!fim03List.isEmpty()) {
                        int y=10;
                    }
                }
            } catch (IOException ex) {
                break;
            }
        }
    }
        
    
    public static void main(String[] args) throws IOException {
        DataFieldDictionary.getInstance().addDefinitions(DataFieldDefinition.read("datafields.txt"));
        SystemClock.getInstance().setReplayMode();
        JTIDSInitData jtidsInitData=new JTIDSInitData();
        MIDSInitData midsInitData=new MIDSInitData();
        
        InitDataChangeMapper mapper = new InitDataChangeMapper(jtidsInitData, midsInitData);
        mapper.read("_init.jdf");
        
        test_1(mapper);
        test_2(mapper);
    }
}
