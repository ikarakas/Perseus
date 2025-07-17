/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.types;

/**
 *
 * @author mike
 */
public enum PackingLimit {
    NO_STATEMENT,
    STD,
    P2_DP,
    P2_SP,
    P4;
    public static FieldType<PackingLimit> TYPE = new FieldType<>() {
        @Override
        public int getLength() {
            return 3;
        }

        @Override
        public PackingLimit decode(long code) {
            return values()[(int)code];
        }

        @Override
        public long encode(PackingLimit value) {
            return value.ordinal();
        }
        
    };
}
