package com.binus.myaddressbook;

public class AddressBook {
    private String id;
    private String first;
    private String last;
    private String city;
    private String country;
    private String phone;
    private String cell;
    private String email;
    private String image_path;

    public AddressBook(String id, String first, String last, String city, String country, String phone, String cell, String email, String image_path) {
        this.id = id;
        this.first = first;
        this.last = last;
        this.city = city;
        this.country = country;
        this.phone = phone;
        this.cell = cell;
        this.email = email;
        this.image_path = image_path;
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getFirst() {
        return first;
    }

    public void setFirst(String first) {
        this.first = first;
    }

    public String getLast() {
        return last;
    }

    public void setLast(String last) {
        this.last = last;
    }

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public String getCell() {
        return cell;
    }

    public void setCell(String cell) {
        this.cell = cell;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getImage_path() {
        return image_path;
    }

    public void setImage_path(String image_path) {
        this.image_path = image_path;
    }
}
