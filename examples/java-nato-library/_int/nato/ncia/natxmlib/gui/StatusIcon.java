/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.gui;
import java.awt.Color;

/**
 *
 * @author mike
 */
public class StatusIcon implements javax.swing.Icon {
    private Color fgColor;
    private Color bgColor;
    private int   border;

    public final static StatusIcon RED = new StatusIcon(Color.RED);
    public final static StatusIcon GREEN = new StatusIcon(Color.GREEN);
    public final static StatusIcon YELLOW = new StatusIcon(Color.YELLOW);    
    public final static StatusIcon LIGHT_GRAY = new StatusIcon(Color.LIGHT_GRAY);
    
    public StatusIcon(Color fg) {
        this(fg, Color.BLACK, 1);
    }
    public StatusIcon(Color fg, int b) {
        this(fg, Color.BLACK, b);
    }
    public StatusIcon(Color fg, Color bg) {
        this(fg, bg, 1);
    }
    public StatusIcon(Color fg, Color bg, int b) {
        fgColor = fg;
        bgColor = bg;
        border = b;
    }

    public void setFgColor(Color fg) {
        fgColor = fg;
    }
    public Color getFgColor() {
        return fgColor;
    }
    public void setBgColor(Color bg) {
        bgColor = bg;
    }
    public Color getBgColor() {
        return bgColor;
    }
    public void setBorder(int b) {
        border = b;
    }
    public int getBorder() {
        return border;
    }

    @Override
    public int getIconWidth() {
        return 11;
    }
    @Override
    public int getIconHeight() {
        return 11;
    }

    @Override
    public void paintIcon(java.awt.Component c, java.awt.Graphics g, int x, int y) {
        g.setColor(bgColor);
        g.fillRect(x, y, getIconWidth(), getIconHeight());
        g.setColor(fgColor);
        g.fillRect(x+border, y+border, getIconWidth()-(2*border), getIconHeight()-(2*border));
    }
}
