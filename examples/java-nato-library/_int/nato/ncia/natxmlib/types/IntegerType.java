/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.types;


/**
 *
 * @author mike
 */
public class IntegerType implements FieldType<Integer>{
    public final int length;

    public IntegerType(int length) {
        this.length = length;
    }
    
    @Override
    public Integer decode(long code) {
        return (int)(code & ((1<<length)-1));
    }

    @Override
    public long encode(Integer value) {
        return (long)(value & ((1<<length)-1));
    }

    @Override
    public int getLength() {
        return length;
    }
    
}
