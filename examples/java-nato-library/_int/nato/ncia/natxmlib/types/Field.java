/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Interface.java to edit this template
 */
package _int.nato.ncia.natxmlib.types;

/**
 *
 * @author mike
 */
public interface Field<K> {
    FieldType<K> getType();
    K getValue();
    long getCode();
    int getOffset();
    int getLength();
    default void setCode(long code) {
        
    }
    default void setValue(K value) {
        
    }
}
