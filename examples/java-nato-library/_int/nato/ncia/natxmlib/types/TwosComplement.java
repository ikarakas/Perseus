package _int.nato.ncia.natxmlib.types;




public class TwosComplement  {
    protected int length;
    protected double factor;
    protected int code;
    
    public TwosComplement(int length, double factor, int code) {
        this.code=code;
        this.length=length;
        this.factor=factor;
    }

    private int getSignedValue() {
        return (code & ((1 << (length - 1)) - 1));
    }

    private boolean isNegative() {
        return (((code >>> (length - 1)) & 0x01) == 1);
    }

    public double getValue() {
        if (isNegative()) {
            return (getSignedValue() - (1 << (length- 1))) * factor;
        } else {
            return getSignedValue() * factor;
        }
    }

    public void setValue(double dValue) {
        int value = (int) (dValue / factor);
        if (value == 0) {
            code=0;
        } else if (value > 0) {
            code=(length == 32 ? value : ((value & ((1 << length) - 1))));
        } else {
            code=((1 << (length - 1)) | (value & ((1 << (length - 1)) - 1)));
        }
    }    

}
