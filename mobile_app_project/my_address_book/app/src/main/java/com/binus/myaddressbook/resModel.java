package com.binus.myaddressbook;

import java.util.ArrayList;

public class resModel {
    private Integer statusCode;
    private String nim;
    private String nama;
    private String employeeId;
    private String credits;
    private ArrayList<Employee> employees;

    public resModel(Integer statusCode, String nim, String nama, String employeeId, String credits, ArrayList<Employee> employees) {
        this.statusCode = statusCode;
        this.nim = nim;
        this.nama = nama;
        this.employeeId = employeeId;
        this.credits = credits;
        this.employees = employees;
    }

    public Integer getStatusCode() {
        return statusCode;
    }

    public void setStatusCode(Integer statusCode) {
        this.statusCode = statusCode;
    }

    public String getNim() {
        return nim;
    }

    public void setNim(String nim) {
        this.nim = nim;
    }

    public String getNama() {
        return nama;
    }

    public void setNama(String nama) {
        this.nama = nama;
    }

    public String getEmployeeId() {
        return employeeId;
    }

    public void setEmployeeId(String employeeId) {
        this.employeeId = employeeId;
    }

    public String getCredits() {
        return credits;
    }

    public void setCredits(String credits) {
        this.credits = credits;
    }

    public ArrayList<Employee> getEmployees() {
        return employees;
    }

    public void setEmployees(ArrayList<Employee> employees) {
        this.employees = employees;
    }
}
