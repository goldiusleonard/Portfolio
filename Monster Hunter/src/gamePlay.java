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
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.awt.event.ActionEvent;
import java.awt.Component;
import java.awt.Dimension;

import javax.swing.Box;
import javax.swing.border.BevelBorder;
import javax.swing.border.SoftBevelBorder;

import javax.swing.border.MatteBorder;
import java.awt.ComponentOrientation;
import javax.swing.JTextArea;
import javax.swing.BoxLayout;
import javax.swing.JProgressBar;
import javax.swing.border.EtchedBorder;
import javax.swing.JTextField;

public class gamePlay extends JFrame{

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private JPanel contentPane;
	private JPanel playerPanel;
	private JPanel monsterPanel;
	private JPanel midPanel;
	private JPanel StatusPanel;
	private JPanel titlePanel;
	
	private JLabel titleLabel;
	
	private JLabel statusLabel;
	
	private JLabel MonsterLabel;
	private JLabel monsterLevelLabel;
	private JLabel monsterHealthLabel;
	private JProgressBar monsterHealthBar;
	private JLabel monsterAtkLabel;
	private JLabel monsterAtkStatLabel;
	private JLabel monsterDefLabel;
	private JLabel monsterDefStatLabel;
	
	private JLabel playerLabel;
	private JLabel playerLevelLabel;
	private JLabel playerHealthLabel;
	private JProgressBar playerHealthBar;
	private JLabel playerExpLabel;
	private JProgressBar playerExpBar;
	private JLabel playerAtkLabel;
	private JLabel playerAtkStatLabel;
	private JLabel playerDefLabel;
	private JLabel playerDefStatLabel;
	
	private JButton saveExitButton;
	
	private Player player;
	private Monster monster;
	
	public JPanel getContentPane() {
		return contentPane;
	}
	
	public gamePlay(String saveprogress) {
		setResizable(true);
		setAlwaysOnTop(false);
		setFocusable(true);
		
		contentPane = new JPanel();
		contentPane.setBackground(new Color(255, 160, 122));
		contentPane.setBorder(null);
		setContentPane(contentPane);
		
		player = new Player();
		monster = new Monster();
		Long temp;
		Long temp2;
		
		if(saveprogress.contentEquals("continue")) {
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
			} catch(IOException ex){
				
			} catch(ClassNotFoundException ex) {
				
	        }
		}
		
		Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
		int screenWidth = (int)screenSize.getWidth();
		int screenHeight = (int)screenSize.getHeight();
		
		setMinimumSize(new Dimension(screenWidth, screenHeight));
		setMaximumSize(new Dimension(screenWidth, screenHeight));
		
		playerPanel = new JPanel();
		playerPanel.setBorder(new LineBorder(new Color(0, 0, 0), 4, true));
		playerPanel.setBackground(new Color(65, 105, 225));
		
		monsterPanel = new JPanel();
		monsterPanel.setBorder(new LineBorder(new Color(0, 0, 0), 4, true));
		monsterPanel.setBackground(new Color(128, 0, 0));
		
		MonsterLabel = new JLabel("Monster Stats");
		MonsterLabel.setForeground(new Color(255, 255, 255));
		MonsterLabel.setHorizontalAlignment(SwingConstants.CENTER);
		MonsterLabel.setFont(new Font("Tekton Pro", Font.BOLD, 30));
		
		monsterLevelLabel = new JLabel("Level 1");
		monsterLevelLabel.setHorizontalAlignment(SwingConstants.CENTER);
		monsterLevelLabel.setForeground(Color.WHITE);
		monsterLevelLabel.setFont(new Font("Tekton Pro", Font.BOLD, 22));
		
		monsterHealthLabel = new JLabel("Health");
		monsterHealthLabel.setHorizontalAlignment(SwingConstants.LEFT);
		monsterHealthLabel.setForeground(Color.WHITE);
		monsterHealthLabel.setFont(new Font("Tekton Pro", Font.BOLD, 22));
		
		monsterHealthBar = new JProgressBar();
		monsterHealthBar.setStringPainted(true);
		monsterHealthBar.setForeground(new Color(0, 128, 0));
		monsterHealthBar.setMinimum(0);
		monsterHealthBar.setMaximum((int)monster.getMaxHealth());
		monsterHealthBar.setValue((int)monster.getHealth());
		
		monsterAtkLabel = new JLabel("Atk");
		monsterAtkLabel.setHorizontalAlignment(SwingConstants.LEFT);
		monsterAtkLabel.setForeground(Color.WHITE);
		monsterAtkLabel.setFont(new Font("Tekton Pro", Font.BOLD, 22));
		
		monsterAtkStatLabel = new JLabel("0");
		monsterAtkStatLabel.setHorizontalAlignment(SwingConstants.RIGHT);
		monsterAtkStatLabel.setForeground(Color.WHITE);
		monsterAtkStatLabel.setFont(new Font("Tekton Pro", Font.PLAIN, 20));
		monsterAtkStatLabel.setBackground(Color.WHITE);
		temp = monster.getAtk();
		monsterAtkStatLabel.setText(temp.toString());
		
		monsterDefLabel = new JLabel("Def");
		monsterDefLabel.setHorizontalAlignment(SwingConstants.LEFT);
		monsterDefLabel.setForeground(Color.WHITE);
		monsterDefLabel.setFont(new Font("Tekton Pro", Font.BOLD, 22));
		
		monsterDefStatLabel = new JLabel("0");
		monsterDefStatLabel.setHorizontalAlignment(SwingConstants.RIGHT);
		monsterDefStatLabel.setForeground(Color.WHITE);
		monsterDefStatLabel.setFont(new Font("Tekton Pro", Font.PLAIN, 20));
		monsterDefStatLabel.setBackground(Color.WHITE);
		temp = monster.getDef();
		monsterDefStatLabel.setText(temp.toString());
		
		GroupLayout gl_monsterPanel = new GroupLayout(monsterPanel);
		gl_monsterPanel.setHorizontalGroup(
			gl_monsterPanel.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_monsterPanel.createSequentialGroup()
					.addGap(17)
					.addGroup(gl_monsterPanel.createParallelGroup(Alignment.TRAILING)
						.addGroup(gl_monsterPanel.createSequentialGroup()
							.addComponent(monsterAtkLabel, GroupLayout.DEFAULT_SIZE, 97, Short.MAX_VALUE)
							.addPreferredGap(ComponentPlacement.UNRELATED)
							.addComponent(monsterAtkStatLabel, GroupLayout.DEFAULT_SIZE, 99, Short.MAX_VALUE))
						.addGroup(gl_monsterPanel.createSequentialGroup()
							.addPreferredGap(ComponentPlacement.RELATED)
							.addComponent(monsterDefLabel, GroupLayout.DEFAULT_SIZE, 97, Short.MAX_VALUE)
							.addPreferredGap(ComponentPlacement.UNRELATED)
							.addComponent(monsterDefStatLabel, GroupLayout.DEFAULT_SIZE, 99, Short.MAX_VALUE))
						.addGroup(gl_monsterPanel.createSequentialGroup()
							.addComponent(monsterHealthLabel, GroupLayout.DEFAULT_SIZE, 108, Short.MAX_VALUE)
							.addPreferredGap(ComponentPlacement.UNRELATED)
							.addComponent(monsterHealthBar, GroupLayout.PREFERRED_SIZE, 88, GroupLayout.PREFERRED_SIZE)))
					.addGap(26))
				.addGroup(gl_monsterPanel.createSequentialGroup()
					.addGap(18)
					.addComponent(MonsterLabel, GroupLayout.DEFAULT_SIZE, 213, Short.MAX_VALUE)
					.addGap(18))
				.addGroup(Alignment.TRAILING, gl_monsterPanel.createSequentialGroup()
					.addGap(79)
					.addComponent(monsterLevelLabel, GroupLayout.DEFAULT_SIZE, 102, Short.MAX_VALUE)
					.addGap(68))
		);
		gl_monsterPanel.setVerticalGroup(
			gl_monsterPanel.createParallelGroup(Alignment.TRAILING)
				.addGroup(gl_monsterPanel.createSequentialGroup()
					.addGap(19)
					.addComponent(MonsterLabel, GroupLayout.PREFERRED_SIZE, 250, GroupLayout.PREFERRED_SIZE)
					.addGap(27)
					.addComponent(monsterLevelLabel, GroupLayout.DEFAULT_SIZE, 47, Short.MAX_VALUE)
					.addGap(118)
					.addGroup(gl_monsterPanel.createParallelGroup(Alignment.BASELINE)
						.addComponent(monsterHealthLabel, GroupLayout.DEFAULT_SIZE, 29, Short.MAX_VALUE)
						.addComponent(monsterHealthBar, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE))
					.addGap(35)
					.addGroup(gl_monsterPanel.createParallelGroup(Alignment.BASELINE)
						.addComponent(monsterAtkLabel, GroupLayout.DEFAULT_SIZE, 31, Short.MAX_VALUE)
						.addComponent(monsterAtkStatLabel, GroupLayout.DEFAULT_SIZE, 25, Short.MAX_VALUE))
					.addGap(31)
					.addGroup(gl_monsterPanel.createParallelGroup(Alignment.BASELINE)
						.addComponent(monsterDefLabel, GroupLayout.PREFERRED_SIZE, 52, GroupLayout.PREFERRED_SIZE)
						.addComponent(monsterDefStatLabel, GroupLayout.DEFAULT_SIZE, 25, Short.MAX_VALUE))
					.addContainerGap())
		);
		monsterPanel.setLayout(gl_monsterPanel);
		
		JPanel midPanel = new JPanel();
		midPanel.setBackground(new Color(255, 228, 181));
		
		StatusPanel = new JPanel();
		StatusPanel.setBorder(new EtchedBorder(EtchedBorder.LOWERED, new Color(128, 128, 128), new Color(255, 255, 255)));
		StatusPanel.setBackground(new Color(255, 140, 0));
		
		titlePanel = new JPanel();
		titlePanel.setBorder(new LineBorder(new Color(245, 255, 250), 10, true));
		titlePanel.setBackground(new Color(165, 42, 42));
		titlePanel.setLayout(new BorderLayout(0, 0));
		
		GroupLayout gl_contentPane = new GroupLayout(contentPane);
		gl_contentPane.setHorizontalGroup(
			gl_contentPane.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_contentPane.createSequentialGroup()
					.addContainerGap()
					.addComponent(playerPanel, GroupLayout.PREFERRED_SIZE, 226, GroupLayout.PREFERRED_SIZE)
					.addPreferredGap(ComponentPlacement.RELATED)
					.addGroup(gl_contentPane.createParallelGroup(Alignment.LEADING)
						.addComponent(midPanel, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
						.addComponent(StatusPanel, GroupLayout.DEFAULT_SIZE, 658, Short.MAX_VALUE)
						.addComponent(titlePanel, Alignment.TRAILING, GroupLayout.DEFAULT_SIZE, 658, Short.MAX_VALUE))
					.addPreferredGap(ComponentPlacement.UNRELATED)
					.addComponent(monsterPanel, GroupLayout.PREFERRED_SIZE, 257, GroupLayout.PREFERRED_SIZE)
					.addContainerGap())
		);
		gl_contentPane.setVerticalGroup(
			gl_contentPane.createParallelGroup(Alignment.TRAILING)
				.addGroup(gl_contentPane.createSequentialGroup()
					.addContainerGap()
					.addGroup(gl_contentPane.createParallelGroup(Alignment.LEADING)
						.addComponent(monsterPanel, GroupLayout.DEFAULT_SIZE, GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
						.addComponent(playerPanel, GroupLayout.DEFAULT_SIZE, 657, Short.MAX_VALUE)
						.addGroup(gl_contentPane.createSequentialGroup()
							.addComponent(titlePanel, GroupLayout.DEFAULT_SIZE, 124, Short.MAX_VALUE)
							.addPreferredGap(ComponentPlacement.UNRELATED)
							.addComponent(midPanel, GroupLayout.DEFAULT_SIZE, 435, Short.MAX_VALUE)
							.addPreferredGap(ComponentPlacement.UNRELATED)
							.addComponent(StatusPanel, GroupLayout.DEFAULT_SIZE, 60, Short.MAX_VALUE)))
					.addGap(28))
		);
		
		titleLabel = new JLabel("MONSTER HUNTER");
		titleLabel.setHorizontalAlignment(SwingConstants.CENTER);
		titleLabel.setForeground(new Color(224, 255, 255));
		titleLabel.setFont(new Font("Tekton Pro", Font.BOLD | Font.ITALIC, 64));
		titleLabel.setBorder(new LineBorder(new Color(0, 0, 0), 0));
		titleLabel.setBackground(new Color(165, 42, 42));
		titleLabel.setAlignmentX(0.5f);
		titlePanel.add(titleLabel, BorderLayout.CENTER);
		
		JButton saveExitButton = new JButton("Save & Exit");
		saveExitButton.setForeground(new Color(139, 69, 19));
		saveExitButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				try {
					String playerFileName = "player.ser";
		            String monsterFileName = "monster.ser";
		            
					FileOutputStream playerSaveFile = new FileOutputStream(playerFileName);
		            ObjectOutputStream playerOut = new ObjectOutputStream(playerSaveFile);
		            
		            FileOutputStream monsterSaveFile = new FileOutputStream(monsterFileName);
		            ObjectOutputStream monsterOut = new ObjectOutputStream(monsterSaveFile);
		            
		            playerOut.writeObject(player);
		            monsterOut.writeObject(monster);
		            
		            playerOut.close();
		            playerSaveFile.close();
		            
		            monsterOut.close();
		            monsterSaveFile.close();
		        } catch(IOException ex) {
		        	
		        }
				System.exit(0);
			}
		});
		saveExitButton.setBackground(new Color(220, 220, 220));
		saveExitButton.setFont(new Font("Tekton Pro", Font.PLAIN, 20));
		saveExitButton.setBorder(new LineBorder(new Color(0, 0, 0), 4, true));
		
		JButton saveButton = new JButton("Save");
		saveButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				try {
					String playerFileName = "player.ser";
		            String monsterFileName = "monster.ser";
		            
					FileOutputStream playerSaveFile = new FileOutputStream(playerFileName);
		            ObjectOutputStream playerOut = new ObjectOutputStream(playerSaveFile);
		            
		            FileOutputStream monsterSaveFile = new FileOutputStream(monsterFileName);
		            ObjectOutputStream monsterOut = new ObjectOutputStream(monsterSaveFile);
		            
		            playerOut.writeObject(player);
		            monsterOut.writeObject(monster);
		            
		            playerOut.close();
		            playerSaveFile.close();
		            
		            monsterOut.close();
		            monsterSaveFile.close();
		        } catch(IOException ex) {
		        	
		        }
			}
		});
		saveButton.setForeground(new Color(139, 69, 19));
		saveButton.setFont(new Font("Tekton Pro", Font.PLAIN, 20));
		saveButton.setBorder(new LineBorder(new Color(0, 0, 0), 4, true));
		saveButton.setBackground(new Color(220, 220, 220));
		
		JButton exitButton = new JButton("Exit");
		exitButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				System.exit(0);
			}
		});
		exitButton.setForeground(new Color(139, 69, 19));
		exitButton.setFont(new Font("Tekton Pro", Font.PLAIN, 20));
		exitButton.setBorder(new LineBorder(new Color(0, 0, 0), 4, true));
		exitButton.setBackground(new Color(220, 220, 220));
		
		GroupLayout gl_midPanel = new GroupLayout(midPanel);
		gl_midPanel.setHorizontalGroup(
			gl_midPanel.createParallelGroup(Alignment.TRAILING)
				.addGroup(Alignment.LEADING, gl_midPanel.createSequentialGroup()
					.addGap(236)
					.addGroup(gl_midPanel.createParallelGroup(Alignment.LEADING)
						.addGroup(gl_midPanel.createSequentialGroup()
							.addComponent(exitButton, GroupLayout.PREFERRED_SIZE, 0, Short.MAX_VALUE)
							.addGap(248))
						.addGroup(gl_midPanel.createSequentialGroup()
							.addGroup(gl_midPanel.createParallelGroup(Alignment.LEADING)
								.addComponent(saveExitButton, Alignment.TRAILING, GroupLayout.DEFAULT_SIZE, 174, Short.MAX_VALUE)
								.addComponent(saveButton, Alignment.TRAILING, GroupLayout.DEFAULT_SIZE, 174, Short.MAX_VALUE))
							.addGap(248))))
		);
		gl_midPanel.setVerticalGroup(
			gl_midPanel.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_midPanel.createSequentialGroup()
					.addGap(80)
					.addComponent(saveButton, GroupLayout.DEFAULT_SIZE, 60, Short.MAX_VALUE)
					.addGap(40)
					.addComponent(saveExitButton, GroupLayout.DEFAULT_SIZE, 60, Short.MAX_VALUE)
					.addGap(41)
					.addComponent(exitButton, GroupLayout.DEFAULT_SIZE, 60, Short.MAX_VALUE)
					.addGap(100))
		);
		midPanel.setLayout(gl_midPanel);
		StatusPanel.setLayout(new BorderLayout(0, 0));
		
		statusLabel = new JLabel("Status Label");
		statusLabel.setBackground(new Color(112, 128, 144));
		statusLabel.setFont(new Font("Tekton Pro", Font.PLAIN, 18));
		statusLabel.setHorizontalAlignment(SwingConstants.CENTER);
		StatusPanel.add(statusLabel, BorderLayout.CENTER);
		
		playerLabel = new JLabel("Player Stats");
		playerLabel.setForeground(new Color(255, 255, 255));
		playerLabel.setHorizontalAlignment(SwingConstants.CENTER);
		playerLabel.setFont(new Font("Tekton Pro", Font.BOLD, 30));
		
		playerHealthLabel = new JLabel("Health");
		playerHealthLabel.setForeground(new Color(255, 255, 255));
		playerHealthLabel.setFont(new Font("Tekton Pro", Font.BOLD, 22));
		playerHealthLabel.setHorizontalAlignment(SwingConstants.LEFT);
		
		playerHealthBar = new JProgressBar();
		playerHealthBar.setStringPainted(true);
		playerHealthBar.setForeground(new Color(0, 128, 0));
		playerHealthBar.setMinimum(0);
		playerHealthBar.setMaximum((int)player.getMaxHealth());
		playerHealthBar.setValue((int)player.getHealth());
		
		playerAtkLabel = new JLabel("Atk");
		playerAtkLabel.setHorizontalAlignment(SwingConstants.LEFT);
		playerAtkLabel.setForeground(Color.WHITE);
		playerAtkLabel.setFont(new Font("Tekton Pro", Font.BOLD, 22));
		
		playerLevelLabel = new JLabel("Level 1");
		playerLevelLabel.setHorizontalAlignment(SwingConstants.CENTER);
		playerLevelLabel.setForeground(Color.WHITE);
		playerLevelLabel.setFont(new Font("Tekton Pro", Font.BOLD, 22));
		temp = player.getLevel();
		playerLevelLabel.setText("Level " + temp.toString());
		
		playerAtkStatLabel = new JLabel("0");
		playerAtkStatLabel.setHorizontalAlignment(SwingConstants.RIGHT);
		playerAtkStatLabel.setForeground(new Color(255, 255, 255));
		playerAtkStatLabel.setFont(new Font("Tekton Pro", Font.PLAIN, 20));
		playerAtkStatLabel.setBackground(new Color(255, 255, 255));
		temp = player.getAtk();
		playerAtkStatLabel.setText(temp.toString());
		
		playerDefLabel = new JLabel("Def");
		playerDefLabel.setHorizontalAlignment(SwingConstants.LEFT);
		playerDefLabel.setForeground(Color.WHITE);
		playerDefLabel.setFont(new Font("Tekton Pro", Font.BOLD, 22));
		
		playerDefStatLabel = new JLabel("0");
		playerDefStatLabel.setHorizontalAlignment(SwingConstants.RIGHT);
		playerDefStatLabel.setForeground(Color.WHITE);
		playerDefStatLabel.setFont(new Font("Tekton Pro", Font.PLAIN, 20));
		playerDefStatLabel.setBackground(Color.WHITE);
		temp = player.getDef();
		playerDefStatLabel.setText(temp.toString());
		
		playerExpLabel = new JLabel("Exp");
		playerExpLabel.setHorizontalAlignment(SwingConstants.LEFT);
		playerExpLabel.setForeground(Color.WHITE);
		playerExpLabel.setFont(new Font("Tekton Pro", Font.BOLD, 22));
		
		playerExpBar = new JProgressBar();
		playerExpBar.setMinimum(0);
		playerExpBar.setMaximum((int)player.getMaxExp());
		playerExpBar.setValue((int)player.getExp());
		playerExpBar.setStringPainted(true);
		playerExpBar.setForeground(new Color(139, 0, 0));
		
		temp = player.getExp();
		temp2 = player.getMaxExp();
		playerExpBar.setString(temp.toString() + "/" + temp2.toString());
		
		GroupLayout gl_playerPanel = new GroupLayout(playerPanel);
		gl_playerPanel.setHorizontalGroup(
			gl_playerPanel.createParallelGroup(Alignment.TRAILING)
				.addGroup(gl_playerPanel.createSequentialGroup()
					.addGroup(gl_playerPanel.createParallelGroup(Alignment.LEADING)
						.addGroup(gl_playerPanel.createSequentialGroup()
							.addContainerGap()
							.addComponent(playerLabel, GroupLayout.DEFAULT_SIZE, 198, Short.MAX_VALUE))
						.addGroup(gl_playerPanel.createSequentialGroup()
							.addGap(17)
							.addComponent(playerDefLabel, GroupLayout.DEFAULT_SIZE, 96, Short.MAX_VALUE)
							.addPreferredGap(ComponentPlacement.RELATED)
							.addComponent(playerDefStatLabel, GroupLayout.DEFAULT_SIZE, 89, Short.MAX_VALUE)))
					.addContainerGap())
				.addGroup(gl_playerPanel.createSequentialGroup()
					.addGap(17)
					.addComponent(playerHealthLabel, GroupLayout.DEFAULT_SIZE, 79, Short.MAX_VALUE)
					.addPreferredGap(ComponentPlacement.UNRELATED)
					.addComponent(playerHealthBar, GroupLayout.DEFAULT_SIZE, 102, Short.MAX_VALUE)
					.addContainerGap())
				.addGroup(gl_playerPanel.createSequentialGroup()
					.addGap(17)
					.addComponent(playerExpLabel, GroupLayout.DEFAULT_SIZE, 83, Short.MAX_VALUE)
					.addPreferredGap(ComponentPlacement.RELATED)
					.addComponent(playerExpBar, GroupLayout.DEFAULT_SIZE, 104, Short.MAX_VALUE)
					.addContainerGap())
				.addGroup(gl_playerPanel.createSequentialGroup()
					.addGap(17)
					.addGroup(gl_playerPanel.createParallelGroup(Alignment.LEADING)
						.addGroup(gl_playerPanel.createSequentialGroup()
							.addGap(95)
							.addComponent(playerAtkStatLabel, GroupLayout.DEFAULT_SIZE, 96, Short.MAX_VALUE))
						.addGroup(gl_playerPanel.createSequentialGroup()
							.addComponent(playerAtkLabel, GroupLayout.DEFAULT_SIZE, 108, Short.MAX_VALUE)
							.addGap(83)))
					.addContainerGap())
				.addGroup(gl_playerPanel.createSequentialGroup()
					.addGap(59)
					.addComponent(playerLevelLabel, GroupLayout.DEFAULT_SIZE, 103, Short.MAX_VALUE)
					.addGap(56))
		);
		gl_playerPanel.setVerticalGroup(
			gl_playerPanel.createParallelGroup(Alignment.LEADING)
				.addGroup(gl_playerPanel.createSequentialGroup()
					.addContainerGap()
					.addComponent(playerLabel, GroupLayout.PREFERRED_SIZE, 274, GroupLayout.PREFERRED_SIZE)
					.addPreferredGap(ComponentPlacement.RELATED)
					.addComponent(playerLevelLabel, GroupLayout.DEFAULT_SIZE, 40, Short.MAX_VALUE)
					.addGap(114)
					.addGroup(gl_playerPanel.createParallelGroup(Alignment.BASELINE)
						.addComponent(playerHealthLabel, GroupLayout.PREFERRED_SIZE, 31, GroupLayout.PREFERRED_SIZE)
						.addComponent(playerHealthBar, GroupLayout.PREFERRED_SIZE, GroupLayout.DEFAULT_SIZE, GroupLayout.PREFERRED_SIZE))
					.addGap(18)
					.addGroup(gl_playerPanel.createParallelGroup(Alignment.LEADING)
						.addComponent(playerExpLabel, GroupLayout.PREFERRED_SIZE, 34, GroupLayout.PREFERRED_SIZE)
						.addGroup(gl_playerPanel.createSequentialGroup()
							.addGap(6)
							.addComponent(playerExpBar, GroupLayout.PREFERRED_SIZE, 16, GroupLayout.PREFERRED_SIZE)))
					.addGap(18)
					.addGroup(gl_playerPanel.createParallelGroup(Alignment.BASELINE)
						.addComponent(playerAtkLabel, GroupLayout.DEFAULT_SIZE, 34, Short.MAX_VALUE)
						.addComponent(playerAtkStatLabel, GroupLayout.DEFAULT_SIZE, 28, Short.MAX_VALUE))
					.addGap(30)
					.addGroup(gl_playerPanel.createParallelGroup(Alignment.BASELINE)
						.addComponent(playerDefLabel, GroupLayout.DEFAULT_SIZE, 31, Short.MAX_VALUE)
						.addComponent(playerDefStatLabel, GroupLayout.DEFAULT_SIZE, 25, Short.MAX_VALUE))
					.addContainerGap())
		);
		playerPanel.setLayout(gl_playerPanel);
		contentPane.setLayout(gl_contentPane);
		
		ExecutorService executor = Executors.newFixedThreadPool(2);
		executor.execute(new playerAttackThread());
		executor.execute(new monsterAttackThread());
		executor.shutdown();
		
	}
	
	public class playerAttackThread implements Runnable {

		@Override
		public void run() {
			// TODO Auto-generated method stub
			long expGain;
			
			while(player.getHealth() > 0 && monster.getHealth() > 0) {
				try {
					player.attack(monster);
					statusLabel.setText("Player attacked the monster!");
					updateScreen();
					
					if(monster.getHealth() <= 0 && player.getHealth() > 0) {
						expGain = monster.countExpForPlayer();
						if(player.getExp() + expGain < player.getMaxExp()) {
							player.setExp(player.getExp() + expGain);
							
							statusLabel.setText("Player defeated the monster. You got " + expGain + " Exp!");
							monster.setLevel(monster.getLevel() + 1);
							monster.updateStat(monster.getLevel());
						}
						else {
							player.setExp(expGain - (player.getMaxExp() - player.getExp()));
							player.setLevel(player.getLevel() + 1);
							player.updateStat(player.getLevel());
							statusLabel.setText("Player defeated the monster. You got " + expGain + " Exp & leveled up!");
							
							monster.setLevel(monster.getLevel() + 1);
							monster.updateStat(monster.getLevel());
						}
						
						player.revive();
						monster.revive();
						updateScreen();
					}
					if(monster.getHealth() <= 0 || player.getHealth() <= 0){
						player.revive();
						monster.revive();
					}
					
					Thread.sleep(800);
				} catch (InterruptedException ie){
					ie.printStackTrace();
				}
			}
			
		}
		
	}
	
	public class monsterAttackThread implements Runnable {

		@Override
		public void run() {
			// TODO Auto-generated method stub
			long expGain;
			
			while(player.getHealth() > 0 && monster.getHealth() > 0) {
				try {
					monster.attack(player);
					statusLabel.setText("Monster attacked the player!");
					updateScreen();
					
					if(monster.getHealth() > 0 && player.getHealth() <= 0) {
						expGain = monster.countExpForPlayer()/2;
						
						if(player.getExp() + expGain < player.getMaxExp()) {
							player.setExp(player.getExp() + expGain);
							
							statusLabel.setText("You die. You got " + expGain + " Exp!");
						}
						else {
							player.setExp(expGain - (player.getMaxExp() - player.getExp()));
							player.setLevel(player.getLevel() + 1);
							player.updateStat(player.getLevel());
							statusLabel.setText("You die. You got " + expGain + " Exp & leveled up!");
						}
						
						
						updateScreen();
						player.revive();
						monster.revive();
					}
					
					if(monster.getHealth() <= 0 || player.getHealth() <= 0){
						player.revive();
						monster.revive();
					}
					
					Thread.sleep(1000);
				} catch (InterruptedException ie){
					ie.printStackTrace();
				}
			}
		}
		
	}
	
	private void updateScreen() {
		playerHealthBar.setMinimum(0);
		playerHealthBar.setMaximum((int)player.getMaxHealth());
		playerHealthBar.setValue((int)player.getHealth());
		
		playerExpBar.setMinimum(0);
		playerExpBar.setMaximum((int)player.getMaxExp());
		playerExpBar.setValue((int)player.getExp());
		Long temp = player.getExp();
		Long temp2 = player.getMaxExp();
		playerExpBar.setString(temp.toString() + "/" + temp2.toString());
		
		monsterHealthBar.setMinimum(0);
		monsterHealthBar.setMaximum((int)monster.getMaxHealth());
		monsterHealthBar.setValue((int)monster.getHealth());
		
		temp = player.getLevel();
		playerLevelLabel.setText("Level " + temp.toString());
		
		temp = player.getAtk();
		playerAtkStatLabel.setText(temp.toString());
		
		temp = player.getDef();
		playerDefStatLabel.setText(temp.toString());
		
		temp = monster.getLevel();
		monsterLevelLabel.setText("Level " + temp.toString());
		
		temp = monster.getAtk();
		monsterAtkStatLabel.setText(temp.toString());
		
		temp = monster.getDef();
		monsterDefStatLabel.setText(temp.toString());
	}
}
