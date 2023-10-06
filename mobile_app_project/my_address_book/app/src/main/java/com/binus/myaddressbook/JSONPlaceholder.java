package com.binus.myaddressbook;

import java.util.ArrayList;

import retrofit2.Call;
import retrofit2.http.GET;
import retrofit2.http.Url;

public interface JSONPlaceholder {
    @GET("stage2/people/?nim=2301857102&nama=Goldius_Leonard")
    Call<resModel> getEmployees();

    @GET
    Call<resModel> getEmployee(@Url String url);
}
