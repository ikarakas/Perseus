/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Interface.java to edit this template
 */
package _int.nato.ncia.natxmlib.types;

/**
 *
 * @author mike
 */
public interface FieldType<K> extends DataCodec<K>{
    int getLength();
    default String getText(K value) {
        return value.toString();
    }
    
}
