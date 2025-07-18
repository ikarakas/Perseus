/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.types;

/**
 *
 * @author mike
 */
public class LatitudeType implements FieldType<Double>{

    @Override
    public Double decode(long code) {
        return new TwosComplement(32, 180.0 / (1L << 31), (int)code).getValue();
    }

    @Override
    public long encode(Double value) {
        throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
    }

    @Override
    public int getLength() {
        return 32;
    }
    
}
