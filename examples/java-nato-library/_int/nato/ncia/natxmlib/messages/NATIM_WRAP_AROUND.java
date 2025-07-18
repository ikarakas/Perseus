/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages;

import _int.nato.ncia.natxmlib.HICDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.types.Field;
import java.util.Collections;



/**
 *
 * @author mike
 */
public class NATIM_WRAP_AROUND extends NATIM {
    protected int[] words;

    public NATIM_WRAP_AROUND() {
        this(new int[]{0xEA950B01,0x156AF4D2,0xACB95A2D,0,0,0,0,0,0});
    }    
    public NATIM_WRAP_AROUND(int[] words) {
        this.words = words;
    }
    
    @Override
    public boolean isTIM() {
        return true;
    }
    @Override
    public String getName() {
        return "TIM_WRAP_AROUND";
    }

    @Override
    public int getBlockId() {
        return -1;
    }

    @Override
    public Iterable<Field> fields() {
        return Collections.EMPTY_LIST;
    }
    public static NATIM_WRAP_AROUND decode(JTIDSDataFrame frame) {
        int[] words=new int[9];
        for(int i=0;i<9;i++) {
            words[i]=frame.getWord(i);
        }
        return new NATIM_WRAP_AROUND(words);
    }
    @Override
    public JTIDSDataFrame[] encode() {
        return new JTIDSDataFrame[]{HICDataFrame.fromWords(words)};
    }
    
}
