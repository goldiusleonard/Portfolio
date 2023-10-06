package com.binus.ootd;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.text.TextUtils;
import android.util.Log;
import android.view.View;
import android.widget.ProgressBar;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.huawei.agconnect.config.AGConnectServicesConfig;
import com.huawei.hms.aaid.HmsInstanceId;
import com.huawei.hms.analytics.HiAnalytics;
import com.huawei.hms.analytics.HiAnalyticsInstance;
import com.huawei.hms.analytics.HiAnalyticsTools;
import com.huawei.hms.common.ApiException;
import com.huawei.hms.support.hianalytics.HiAnalyticsUtils;

public class SplashActivity extends AppCompatActivity {
    private static final String TAG = "PushLog";
    private String token;

    private ProgressBar progressBar;
    private FirebaseAuth mAuth;
    private FirebaseUser user;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);
        progressBar = findViewById(R.id.splash_progressBar);

        progressBar.setVisibility(View.VISIBLE);
        mAuth = FirebaseAuth.getInstance();
        user = mAuth.getCurrentUser();

        getToken();
        HiAnalyticsTools.enableLog();

        Context context = this.getApplicationContext();
        HiAnalyticsInstance instance = HiAnalytics.getInstance(context);
        instance.setUserProfile("userKey", token);

        final Handler handler = new Handler();
        handler.postDelayed(new Runnable() {
            @Override
            public void run() {
                if (user == null) {
                    startActivity(new Intent(getApplicationContext(), LoginActivity.class));
                    finish();
                }
                else {
                    startActivity(new Intent(getApplicationContext(), HomeActivity.class));
                    finish();
                }
                progressBar.setVisibility(View.GONE);
            }
        }, 1500);
    }

    private void getToken() {
        new Thread() {
            @Override
            public void run() {
                try {
                    String appId = AGConnectServicesConfig.fromContext(SplashActivity.this).getString("client/app_id");
                    String tokenScope = "HCM";
                    token = HmsInstanceId.getInstance(SplashActivity.this
                    ).getToken(appId, tokenScope);
                    Log.i(TAG, "get token: " + token);

                    if(!TextUtils.isEmpty(token)) {
                        sendRegTokenToServer(token);
                    }

                } catch(ApiException e) {
                    Log.e(TAG, "get token failed, " + e);
                }
            }
        }.start();
    }

    private void sendRegTokenToServer(String token) {
        Log.i(TAG, "sending token to server. token: " + token);
    }

}