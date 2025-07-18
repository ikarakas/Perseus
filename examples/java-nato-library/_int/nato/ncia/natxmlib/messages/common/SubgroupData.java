package _int.nato.ncia.natxmlib.messages.common;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;

/**
 *
 * @author mike
 */
public class SubgroupData {
    
    protected int type;

    public SubgroupData(int type) {
        this.type = type;
    }

    public static SubgroupData decode(JTIDSDataFrame f, int wordOffset) {
        int type = f.getCode(wordOffset, 14, 2);
        switch (type) {
            case 0:
                return new JWordData(f, wordOffset);
            case 1:
                return new CCCSPosition(f, wordOffset);
            default:
                return new SubgroupData(type);
        }
    }
    public void put(JTIDSDataFrame f, int wordOffset) {
        f.setCode(wordOffset, 14, 2, type);
    }
}
