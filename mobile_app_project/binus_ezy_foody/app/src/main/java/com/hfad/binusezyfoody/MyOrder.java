package com.hfad.binusezyfoody;

public class MyOrder {
    private String type;
    private Integer position;
    private Integer quantity;

    public MyOrder(String type, Integer position, Integer quantity) {
        this.type = type;
        this.position = position;
        this.quantity = quantity;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getType() {
        return type;
    }

    public Integer getPosition() {
        return position;
    }

    public void setPosition(Integer position) {
        this.position = position;
    }

    public Integer getQuantity() {
        return quantity;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }
}
