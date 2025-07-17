/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tim4;

/**
 *
 * @author mike
 */
public class NATIM4_RequestRepyRecord_Empty extends NATIM4_RequestReplyRecord {
   public NATIM4_RequestRepyRecord_Empty() {
       super(Format.NO_DATA);
   }

    @Override
    public String toString() {
        return "{format=" + format + '}';
    }
   
}
