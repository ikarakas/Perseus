package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.ginslib.ntdlc.record.Recorder;
import _int.nato.ncia.natxmlib.Config;
import _int.nato.ncia.natxmlib.data.DataFieldDefinition;
import _int.nato.ncia.natxmlib.data.DataFieldDictionary;
import _int.nato.ncia.natxmlib.gui.JTIDSEmulatorGui;
import _int.nato.ncia.natxmlib.gui.JTIDSHostEmulatorGUI;
import _int.nato.ncia.natxmlib.gui.MIDSGatewayGUI;
import _int.nato.ncia.natxmlib.gui.MIDSGatewayMonitorUI;
import java.awt.GraphicsConfiguration;
import java.awt.Insets;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.Toolkit;
import java.io.IOException;
import javax.swing.JFrame;

/**
 *
 * @author mike
 */
public class Main {

    public static void setLocationToTopRight(JFrame frame) {
        GraphicsConfiguration config = frame.getGraphicsConfiguration();
        Rectangle bounds = config.getBounds();
        Insets insets = Toolkit.getDefaultToolkit().getScreenInsets(config);

        int x = bounds.x + bounds.width - insets.right - frame.getWidth();
        int y = bounds.y + insets.top;
        frame.setLocation(x, y);
    }

    public static void JHE_TO_JTE() throws IOException {
        FrameLoop bomLoop = new FrameLoop();
        FrameLoop bimLoop = new FrameLoop();
        JTIDSEmulator je = new JTIDSEmulator(bimLoop, bomLoop);
        JTIDSEmulatorGui jeg = new JTIDSEmulatorGui(je);

        JTIDSHostEmulator jhe = new JTIDSHostEmulator(bomLoop, bimLoop);
        JTIDSHostEmulatorGUI jheg = new JTIDSHostEmulatorGUI(jhe);

        jheg.setVisible(true);
        Point p = jheg.getLocation();
        p.move(jheg.getWidth(), 0);
        jeg.setLocation(p);
        jeg.setVisible(true);

        je.start();
        jhe.start();
    }

    public static void JHE_TO_JMG() throws IOException {
        FrameLoop bomLoop = new FrameLoop();
        FrameLoop bimLoop = new FrameLoop();
        
        JTIDSHostEmulator jhe = new JTIDSHostEmulator(bomLoop, bimLoop);
        MIDSGateway mg = new MIDSGateway(bimLoop, bomLoop);
        
        JTIDSHostEmulatorGUI jheg = new JTIDSHostEmulatorGUI(jhe);
        MIDSGatewayGUI mgg = new MIDSGatewayGUI(mg);
        MIDSGatewayMonitorUI mgmui = new MIDSGatewayMonitorUI(mg);
        
        jheg.setVisible(true);
        Point p = jheg.getLocation();
        p.move(jheg.getWidth(), 0);
        mgg.setLocation(p);
        
        mgg.setVisible(true);
        mgmui.setVisible(true);
        mg.start();
        jhe.start();
    }

    public static void main(String[] args) throws IOException {
        DataFieldDictionary.getInstance().addDefinitions(DataFieldDefinition.read("datafields.txt"));
        Config.getInstance().load("ntdlc.conf");
        Recorder.getInstance().setEnabled(false);
        
        //JHE_TO_JTE();
        JHE_TO_JMG();
    }

}
