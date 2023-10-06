package com.binus.myaddressbook;

public class DOB {
    private String date;
    private Integer age;

    public DOB(String date, Integer age) {
        this.date = date;
        this.age = age;
    }

    public String getDate() {
        return date;
    }

    public void setDate(String date) {
        this.date = date;
    }

    public Integer getAge() {
        return age;
    }

    public void setAge(Integer age) {
        this.age = age;
    }
}
