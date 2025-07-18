/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Interface.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages;

import _int.nato.ncia.natxmlib.types.Field;

/**
 *
 * @author mike
 */
public interface NABxM {
    boolean isBIM();
    int getBlockId();
    int getSubblockId();
    Iterable<Field> fields();
    String getName();
   
}
