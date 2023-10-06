package com.hfad.binusezyfoody;

public class Snack {
    private String name;
    private Integer price;
    private int img;

    public Snack(String name, Integer price, int img) {
        this.name = name;
        this.price = price;
        this.img = img;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    public Integer getPrice() {
        return price;
    }

    public void setPrice(Integer price) {
        this.price = price;
    }

    public void setImg(int img) {
        this.img = img;
    }

    public int getImg() {
        return img;
    }
}
