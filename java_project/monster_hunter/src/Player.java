import java.io.Serializable;

public class Player extends Character implements Serializable {
	private long maxHealth;
	private long health;
	private long maxExp;
	private long exp;
	private long level;
	private long atk;
	private long def;
	
	public Player() {
		super();
		setDefaultStat();
	}
	
	public void attack(Monster monster) {
		monster.setHealth(monster.getHealth()-(getAtk()-monster.getDef()));
	}
	
	@Override
	public long getLevel() {
		return this.level;
	}
	
	public long getMaxExp() {
		return this.maxExp;
	}
	
	public long getExp() {
		return this.exp;
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
		setLevel(1);
		setExp(0);
		setMaxExp(countMaxExp(getLevel()));
		setHealth(countMaxHealth(getLevel()));
		setMaxHealth(countMaxHealth(getLevel()));
		setAtk(countAtk(getLevel()));
		setDef(countDef(getLevel()));
	}
	
	public void updateStat(long level) {
		setLevel(level);
		setMaxExp(countMaxExp(getLevel()));
		setHealth(countMaxHealth(getLevel()));
		setMaxHealth(countMaxHealth(getLevel()));
		setAtk(countAtk(getLevel()));
		setDef(countDef(getLevel()));
	}
	
	public void revive() {
		setHealth(getMaxHealth());
	}
	
	public long countMaxExp(long level) {
		return level*10 + (level-1)*40;
	}
	
	public long countMaxHealth(long level) {
		return 100 + (level-1)*50 + (long)(Math.random()*20);
	}
	
	public long countAtk(long level) {
		return 11 + (level-1)*7 + (long)(Math.random()*4);
	}
	
	public long countDef(long level) {
		return 5 + (level-1)*4 + (long)(Math.random()*2);
	}
	
	@Override
	public void setLevel(long level) {
		// TODO Auto-generated method stub
		this.level = level;
	}
	
	public void setMaxExp(long maxExp) {
		this.maxExp = maxExp;
	}
	
	public void setExp(long exp) {
		// TODO Auto-generated method stub
		this.exp = exp;
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
