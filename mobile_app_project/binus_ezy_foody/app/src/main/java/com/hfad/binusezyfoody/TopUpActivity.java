package com.hfad.binusezyfoody;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;

public class TopUpActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_top_up);
    }

    public void myOrderOnclick(View view) {
        startActivity(new Intent(this, MyOrderActivity.class));
    }

    public void backOnclick(View view) {
        finish();
    }

}