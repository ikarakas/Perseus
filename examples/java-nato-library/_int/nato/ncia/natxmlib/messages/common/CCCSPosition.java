/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.common;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.messages.common.SubgroupData;

/**
 *
 * @author mike
 */
public class CCCSPosition extends SubgroupData {
    
    protected int up_code;
    protected int vp_code;
    protected int uv_code;
    protected int vv_code;

    public CCCSPosition(JTIDSDataFrame f, int wordOffset) {
        super(1);
        up_code = f.getCode(wordOffset, 16, 16);
        vv_code = f.getCode(wordOffset + 1, 0, 16);
        uv_code = f.getCode(wordOffset + 1, 16, 16);
        vp_code = f.getCode(wordOffset + 2, 16, 16);
    }
    
}
