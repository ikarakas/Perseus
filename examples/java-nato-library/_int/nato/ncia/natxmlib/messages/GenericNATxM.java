/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages;

import _int.nato.ncia.natxmlib.types.Field;
import java.util.Arrays;

/**
 *
 * @author mike
 */
public class GenericNATxM implements NATxM {
    protected final boolean tim;
    protected final int id;
    protected final Field[] fields;

    public GenericNATxM(boolean tim, int id, Field[] fields) {
        this.tim = tim;
        this.id = id;
        this.fields = fields;
    }
    
    @Override
    public boolean isTIM() {
        return tim;
    }

    @Override
    public int getBlockId() {
        return id;
    }

    @Override
    public Iterable<Field> fields() {
        return Arrays.asList(fields);
    }

    @Override
    public String getName() {
        return tim?("TIM0"+id):("TOM0"+id);
    }
    
}
