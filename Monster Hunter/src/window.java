import java.awt.BorderLayout;
import java.awt.EventQueue;

import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.border.EmptyBorder;
import java.awt.Font;
import java.awt.Toolkit;
import java.awt.Color;
import javax.swing.JLabel;
import javax.swing.JSplitPane;
import java.awt.FlowLayout;
import javax.swing.border.LineBorder;
import javax.swing.UIManager;
import javax.swing.GroupLayout;
import javax.swing.ImageIcon;
import javax.swing.GroupLayout.Alignment;
import javax.swing.SwingConstants;
import javax.swing.JButton;
import javax.swing.LayoutStyle.ComponentPlacement;
import java.awt.event.ActionListener;
import java.awt.event.ComponentAdapter;
import java.awt.event.ComponentEvent;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.awt.event.ActionEvent;
import java.awt.Component;
import java.awt.Dimension;

import javax.swing.Box;
import javax.swing.border.BevelBorder;
import javax.swing.border.SoftBevelBorder;
import javax.swing.border.MatteBorder;
import java.awt.ComponentOrientation;
import net.miginfocom.swing.MigLayout;
import javax.swing.SpringLayout;
import java.awt.GridBagLayout;
import java.awt.GridBagConstraints;
import java.awt.Insets;

public class window extends JFrame {

	// Created by GOLDIUS LEONARD / 2301857102 / BS01
	// Zero-Player Game
	
	private static final long serialVersionUID = 1L;
	private JPanel contentPane;
	private JPanel menuPanel;
	private JPanel titlePanel;
	private JLabel versionLabel;
	private JLabel titleLabel;
	
	private JButton playButton;
	private JButton continueButton;
	private JButton exitButton;
	
	public static void main(String[] args) {
		EventQueue.invokeLater(new Runnable() {
			public void run() {
				try {
					window frame = new window();
					frame.setVisible(true);
				} catch (Exception e) {
					e.printStackTrace();
				}
			}
		});
	}	
	
	public JPanel getContentPane() {
		return contentPane;
	}
	
	public window() {
		setResizable(true);
		try {
			ImageIcon imgIcon = new ImageIcon("Logo.png");
			setIconImage(imgIcon.getImage());
		} catch(Exception e) {
			
		}
		
		Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
		int screenWidth = (int) screenSize.getWidth();
		int screenHeight = (int) screenSize.getHeight();
		
		setMinimumSize(new Dimension(screenWidth, screenHeight));
		setMaximumSize(new Dimension(screenWidth, screenHeight));
		
		addWindowListener(new WindowAdapter() {
			public void windowActivated(WindowEvent e) {
				toFront();
            }
            
            public void windowDeactivated(WindowEvent e) {
            	toBack();
            }
        });
		
		setLocationRelativeTo(null);
		setBackground(new Color(139, 0, 0));
		setTitle("Monster Hunter");
		setForeground(new Color(139, 0, 0));
		setFont(new Font("Tekton Pro", Font.PLAIN, 12));
		setAlwaysOnTop(true);
		setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		contentPane = new JPanel();
		contentPane.setBackground(new Color(255, 160, 122));
		contentPane.setBorder(null);
		setContentPane(contentPane);
		
		menuPanel = new JPanel();
		menuPanel.setBorder(new LineBorder(new Color(0, 0, 0), 0));
		menuPanel.setBackground(new Color(255, 160, 122));
		
		titlePanel = new JPanel();
		titlePanel.setBorder(new LineBorder(new Color(245, 255, 250), 10, true));
		titlePanel.setBackground(new Color(165, 42, 42));
		titlePanel.setLayout(new BorderLayout(0, 0));
		
		versionLabel = new JLabel("V 1.0");
		versionLabel.setFont(new Font("Tahoma", Font.PLAIN, 18));
		
		GroupLayout gl_contentPane = new GroupLayout(contentPane);
		gl_contentPane.setHorizontalGroup(
			gl_contentPane.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_contentPane.createSequentialGroup()
					.addContainerGap()
					.addComponent(titlePanel, GroupLayout.DEFAULT_SIZE, 1138, Short.MAX_VALUE)
					.addContainerGap())
				.addGroup(gl_contentPane.createSequentialGroup()
					.addContainerGap()
					.addComponent(versionLabel, GroupLayout.DEFAULT_SIZE, 55, Short.MAX_VALUE)
					.addGap(1093))
				.addGroup(gl_contentPane.createSequentialGroup()
					.addGap(378)
					.addComponent(menuPanel, GroupLayout.PREFERRED_SIZE, 376, Short.MAX_VALUE)
					.addGap(404))
		);
		gl_contentPane.setVerticalGroup(
			gl_contentPane.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_contentPane.createSequentialGroup()
					.addContainerGap()
					.addComponent(titlePanel, GroupLayout.DEFAULT_SIZE, 137, Short.MAX_VALUE)
					.addGap(50)
					.addComponent(menuPanel, GroupLayout.DEFAULT_SIZE, 475, Short.MAX_VALUE)
					.addGap(17)
					.addComponent(versionLabel)
					.addGap(0))
		);
		
		titleLabel = new JLabel("MONSTER HUNTER");
		titleLabel.setHorizontalAlignment(SwingConstants.CENTER);
		titleLabel.setForeground(new Color(224, 255, 255));
		titleLabel.setFont(new Font("Tekton Pro", Font.BOLD | Font.ITALIC, 70));
		titleLabel.setBorder(new LineBorder(new Color(0, 0, 0), 0));
		titleLabel.setBackground(new Color(165, 42, 42));
		titleLabel.setAlignmentX(0.5f);
		titlePanel.add(titleLabel, BorderLayout.CENTER);
		
		playButton = new JButton("Play");
		playButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				remove(contentPane);
				
				contentPane = new gamePlay("start").getContentPane();
				
				setContentPane(contentPane);
				contentPane.repaint();
				contentPane.revalidate();
				setVisible(true);
			}
		});
		playButton.setSelected(false);
		playButton.setHideActionText(true);
		playButton.setForeground(new Color(218, 165, 32));
		playButton.setFont(new Font("Tahoma", Font.PLAIN, 40));
		playButton.setBorder(new LineBorder(new Color(0, 0, 0), 6, true));
		playButton.setBackground(new Color(220, 220, 220));
		
		continueButton = new JButton("Continue");
		continueButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				remove(contentPane);
				
				contentPane = new gamePlay("continue").getContentPane();
				
				setContentPane(contentPane);
				contentPane.repaint();
				contentPane.revalidate();
				setVisible(true);
			}
		});
		continueButton.setSelected(false);
		continueButton.setHideActionText(true);
		continueButton.setForeground(new Color(255, 140, 0));
		continueButton.setFont(new Font("Tahoma", Font.PLAIN, 40));
		continueButton.setBorder(new LineBorder(new Color(0, 0, 0), 6, true));
		continueButton.setBackground(new Color(220, 220, 220));
		
		exitButton = new JButton("Exit");
		exitButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				System.exit(0);
			}
		});
		exitButton.setSelected(false);
		exitButton.setHideActionText(true);
		exitButton.setForeground(new Color(128, 0, 0));
		exitButton.setFont(new Font("Tahoma", Font.PLAIN, 40));
		exitButton.setBorder(new LineBorder(new Color(0, 0, 0), 6, true));
		exitButton.setBackground(new Color(220, 220, 220));
		GroupLayout gl_menuPanel = new GroupLayout(menuPanel);
		gl_menuPanel.setHorizontalGroup(
			gl_menuPanel.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_menuPanel.createSequentialGroup()
					.addContainerGap()
					.addComponent(playButton, GroupLayout.DEFAULT_SIZE, 362, Short.MAX_VALUE)
					.addGap(4))
				.addGroup(gl_menuPanel.createSequentialGroup()
					.addGap(7)
					.addGroup(gl_menuPanel.createParallelGroup(Alignment.TRAILING)
						.addComponent(continueButton, Alignment.LEADING, GroupLayout.DEFAULT_SIZE, 362, Short.MAX_VALUE)
						.addComponent(exitButton, Alignment.LEADING, GroupLayout.DEFAULT_SIZE, 362, Short.MAX_VALUE))
					.addGap(7))
		);
		gl_menuPanel.setVerticalGroup(
			gl_menuPanel.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_menuPanel.createSequentialGroup()
					.addGap(20)
					.addComponent(playButton, GroupLayout.DEFAULT_SIZE, 91, Short.MAX_VALUE)
					.addGap(85)
					.addComponent(continueButton, GroupLayout.DEFAULT_SIZE, 94, Short.MAX_VALUE)
					.addGap(83)
					.addComponent(exitButton, GroupLayout.DEFAULT_SIZE, 92, Short.MAX_VALUE)
					.addContainerGap())
		);
		menuPanel.setLayout(gl_menuPanel);
		contentPane.setLayout(gl_contentPane);
		
		// load game
		Player player = new Player();
		Monster monster = new Monster();
		
		try {
            String playerFileName = "player.ser";
            String monsterFileName = "monster.ser";
            
			FileInputStream playerSaveFile = new FileInputStream(playerFileName);
            ObjectInputStream playerIn = new ObjectInputStream(playerSaveFile);
            
            FileInputStream monsterSaveFile = new FileInputStream(monsterFileName);
            ObjectInputStream monsterIn = new ObjectInputStream(monsterSaveFile);
            
            player = (Player)playerIn.readObject();
            monster = (Monster)monsterIn.readObject();
            
            playerIn.close();
            playerSaveFile.close();
            
            monsterIn.close();
            monsterSaveFile.close();
            
            continueButton.setEnabled(true);
		} catch(IOException ex){
			continueButton.setEnabled(false);
		} catch(ClassNotFoundException ex) {
			continueButton.setEnabled(false);
        }
	}
}
