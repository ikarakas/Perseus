/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.types.Field;
import java.util.Collections;



/**
 *
 * @author mike
 */
public class NATOM_Unknown extends NATIM {
    protected int[] words;
    protected int blkId;
    
    public NATOM_Unknown(int blkId, int[] words) {
        this.words = words;
    }
    
    @Override
    public boolean isTIM() {
        return true;
    }
    
    @Override
    public int getBlockId() {
        return blkId;
    }

    @Override
    public Iterable<Field> fields() {
        return Collections.EMPTY_LIST;
    }
    public static NATOM_Unknown decode(JTIDSDataFrame frame) {
        int[] words=new int[9];
        for(int i=0;i<9;i++) {
            words[i]=frame.getWord(i);
        }
        return new NATOM_Unknown(frame.getCode(0,1,5),words);
    }
    
}
