/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages;

import _int.nato.ncia.natxmlib.messages.NATxM;


/**
 *
 * @author mike
 */
public abstract class NATOM implements NATxM {

    @Override
    public boolean isTIM() {
        return false;
    }
    @Override
    public String getName() {
        return "TOM"+getBlockId();
    }
   
    
}
