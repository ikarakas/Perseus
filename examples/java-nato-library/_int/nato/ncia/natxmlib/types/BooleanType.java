/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.types;


/**
 *
 * @author mike
 */
public class BooleanType implements FieldType<Boolean>{

    @Override
    public Boolean decode(long code) {
        return code!=0?Boolean.TRUE:Boolean.FALSE;
    }

    @Override
    public long encode(Boolean value) {
        return value?1:0;
    }

    @Override
    public int getLength() {
        return 1;
    }
    
}
