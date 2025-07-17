/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages;

import _int.nato.ncia.natxmlib.HICDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.types.Field;
import java.util.Arrays;
import java.util.Collections;



/**
 *
 * @author mike
 */
public class NATOM_WRAP_AROUND extends NATOM {
    //EA950B01 156AF4D2 ACB95A2D  00000000 00000000 00000000  00000000 00000000 00000000
    protected int[] words;

    public NATOM_WRAP_AROUND() {
        this(new int[]{0xEA950B01,0x156AF4D2,0xACB95A2D,0,0,0,0,0,0});
    }
    public NATOM_WRAP_AROUND(int[] words) {
        this.words = words;
    }
    public NATOM_WRAP_AROUND(NATIM_WRAP_AROUND tim) {
        this.words=Arrays.copyOfRange(tim.words, 0, tim.words.length);
    }
    @Override
    public boolean isTIM() {
        return false;
    }
    @Override
    public String getName() {
        return "TOM_WRAP_AROUND";
    }

    @Override
    public int getBlockId() {
        return -1;
    }

    @Override
    public Iterable<Field> fields() {
        return Collections.EMPTY_LIST;
    }
    public static NATOM_WRAP_AROUND decode(JTIDSDataFrame frame) {
        int[] words=new int[9];
        for(int i=0;i<9;i++) {
            words[i]=frame.getWord(i);
        }
        return new NATOM_WRAP_AROUND(words);
    }
    @Override
    public JTIDSDataFrame[] encode() {
        return new JTIDSDataFrame[]{HICDataFrame.fromWords(words)};
    }
}
