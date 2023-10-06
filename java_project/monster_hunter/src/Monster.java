import java.io.Serializable;

public class Monster extends Character implements Serializable {
	private long level;
	private long maxHealth;
	private long health;
	private long atk;
	private long def;
	
	public Monster() {
		super();
		setDefaultStat();
	}
	
	public void attack(Player player) {
		player.setHealth(player.getHealth()-(getAtk()-player.getDef()));
	}
	
	@Override
	public long getLevel() {
		return this.level;
	}
	
	@Override
	public long getMaxHealth() {
		// TODO Auto-generated method stub
		return this.maxHealth;
	}
	
	@Override
	public long getHealth() {
		// TODO Auto-generated method stub
		return this.health;
	}

	@Override
	public long getAtk() {
		// TODO Auto-generated method stub
		return this.atk;
	}

	@Override
	public long getDef() {
		// TODO Auto-generated method stub
		return this.def;
	}

	@Override
	public void setDefaultStat() {
		// TODO Auto-generated method stub
		setLevel(1);
		setMaxHealth(countMaxHealth(getLevel()));
		setHealth(countMaxHealth(getLevel()));
		setAtk(countAtk(getLevel()));
		setDef(countDef(getLevel()));
	}
	
	public void updateStat(long level) {
		setLevel(level);
		setMaxHealth(countMaxHealth(getLevel()));
		setHealth(countMaxHealth(getLevel()));
		setAtk(countAtk(getLevel()));
		setDef(countDef(getLevel()));
	}
	
	public void revive() {
		setHealth(getMaxHealth());
	}
	
	public long countMaxHealth(long level) {
		return 80 + (level-1)*40 + (long)(Math.random()*20);
	}
	
	public long countAtk(long level) {
		return 6 + (level-1)*4 + (long)(Math.random()*3);
	}
	
	public long countDef(long level) {
		return 3 + (level-1)*2 + (long)(Math.random()*1);
	}
	
	public long countExpForPlayer() {
		return getLevel()*4*((long)(Math.random()*2 + 1));
	}
	
	@Override
	public void setLevel(long level) {
		// TODO Auto-generated method stub
		this.level = level;
	}
	
	@Override
	public void setMaxHealth(long maxHealth) {
		// TODO Auto-generated method stub
		this.maxHealth = maxHealth;
	}
	
	@Override
	public void setHealth(long health) {
		// TODO Auto-generated method stub
		this.health = health;
	}

	@Override
	public void setAtk(long atk) {
		// TODO Auto-generated method stub
		this.atk = atk;
	}

	@Override
	public void setDef(long def) {
		// TODO Auto-generated method stub
		this.def = def;
	}

}
