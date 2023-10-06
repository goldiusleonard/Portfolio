package com.binus.ootd;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.util.Patterns;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Toast;

import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;
import com.google.firebase.auth.FirebaseAuth;

public class ForgotPasswordActivitiy extends AppCompatActivity {
    private EditText email_textbox;
    private Button resetBtn, loginBtn;
    private ProgressBar progressBar;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_forgot_password);

        email_textbox = findViewById(R.id.forgot_password_email_textbox);
        resetBtn = findViewById(R.id.reset_password_button);
        loginBtn = findViewById(R.id.forgot_password_login_button);
        progressBar = findViewById(R.id.forgot_password_progressBar);

        resetBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String email = email_textbox.getText().toString().trim();
                if (email.isEmpty()) {
                    email_textbox.setError("Email is required!");
                    email_textbox.requestFocus();
                }
                else if (!Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
                    email_textbox.setError("Email is not valid!");
                    email_textbox.requestFocus();
                }
                else {
                    progressBar.setVisibility(View.VISIBLE);
                    FirebaseAuth.getInstance().sendPasswordResetEmail(email)
                            .addOnCompleteListener(new OnCompleteListener<Void>() {
                                @Override
                                public void onComplete(@NonNull Task<Void> task) {
                                    if (task.isSuccessful()) {
                                        Toast.makeText(getApplicationContext(), "Email Sent!", Toast.LENGTH_SHORT).show();
                                        startActivity(new Intent(ForgotPasswordActivitiy.this, LoginActivity.class));
                                        finish();
                                    }
                                    else {
                                        email_textbox.setError("Email is not registered!");
                                        email_textbox.requestFocus();
                                    }
                                    progressBar.setVisibility(View.GONE);
                                }
                            });
                }

            }
        });

        loginBtn.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(ForgotPasswordActivitiy.this, LoginActivity.class));
                finish();
            }
        });

    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
        startActivity(new Intent(ForgotPasswordActivitiy.this, LoginActivity.class));
        finish();
    }
}