package com.binus.ootd;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.service.autofill.UserData;
import android.util.Log;
import android.util.Patterns;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Toast;

import com.google.android.gms.tasks.OnCompleteListener;
import com.google.firebase.auth.AuthResult;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.huawei.hmf.tasks.OnSuccessListener;
import com.huawei.hmf.tasks.Task;
import com.huawei.hms.support.hwid.HuaweiIdAuthManager;
import com.huawei.hms.support.hwid.request.HuaweiIdAuthParams;
import com.huawei.hms.support.hwid.request.HuaweiIdAuthParamsHelper;
import com.huawei.hms.support.hwid.result.AuthHuaweiId;
import com.huawei.hms.support.hwid.service.HuaweiIdAuthService;

public class LoginActivity extends AppCompatActivity {
    private EditText email_textbox, password_textbox;
    private Button login_button;
    private ProgressBar progressBar;

    private HuaweiIdAuthParams authParams;
    private HuaweiIdAuthService service;

    private FirebaseAuth mAuth;
    private FirebaseDatabase rootNode;
    private DatabaseReference userReference;
    private DatabaseReference taskReference;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        email_textbox = findViewById(R.id.login_email_textbox);
        password_textbox = findViewById(R.id.login_password_textbox);
        login_button = findViewById(R.id.login_button);

        progressBar = findViewById(R.id.login_progressBar);
        mAuth = FirebaseAuth.getInstance();
        rootNode = FirebaseDatabase.getInstance();
        userReference = rootNode.getReference("users");
        taskReference = rootNode.getReference("tasks");

        login_button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String emailText = email_textbox.getText().toString().trim();
                String passwordText = password_textbox.getText().toString().trim();

                if (passwordText.isEmpty()) {
                    password_textbox.setError("Password is required!");
                    password_textbox.requestFocus();
                }
                if (emailText.isEmpty()) {
                    email_textbox.setError("Email is required!");
                    email_textbox.requestFocus();
                }
                if (!Patterns.EMAIL_ADDRESS.matcher(emailText).matches()) {
                    email_textbox.setError("Email is not valid!");
                    email_textbox.requestFocus();
                }

                if (!emailText.isEmpty() && !passwordText.isEmpty()) {
                    progressBar.setVisibility(View.VISIBLE);

                    mAuth.signInWithEmailAndPassword(emailText, passwordText).addOnCompleteListener(new OnCompleteListener<AuthResult>() {
                        @Override
                        public void onComplete(@NonNull com.google.android.gms.tasks.Task<AuthResult> task) {
                            if (task.isSuccessful()) {
                                startActivity(new Intent(LoginActivity.this, HomeActivity.class));
                                finish();
                            }
                            else {
                                Toast.makeText(getApplicationContext(), "Invalid Email or Password!", Toast.LENGTH_LONG).show();
                            }
                        }
                    });
                }
                progressBar.setVisibility(View.GONE);
            }
        });

        findViewById(R.id.forgot_password_button).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(LoginActivity.this, ForgotPasswordActivitiy.class));
                finish();
            }
        });

        findViewById(R.id.login_huawei_button).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                progressBar.setVisibility(View.VISIBLE);
                authParams = new HuaweiIdAuthParamsHelper(HuaweiIdAuthParams.DEFAULT_AUTH_REQUEST_PARAM).setUid().setEmail().setProfile().createParams();
                service = HuaweiIdAuthManager.getService(LoginActivity.this, authParams);

                Task<AuthHuaweiId> task = service.silentSignIn();
                task.addOnSuccessListener(new OnSuccessListener<AuthHuaweiId>() {
                    @Override
                    public void onSuccess(AuthHuaweiId authHuaweiId) {
                        String uid = authHuaweiId.getUnionId();
                        String name = authHuaweiId.getDisplayName();
                        String email = authHuaweiId.getEmail();
                        String password = authHuaweiId.getUnionId();

                        mAuth.createUserWithEmailAndPassword(email, password)
                                .addOnCompleteListener(new OnCompleteListener<AuthResult>() {
                                    @Override
                                    public void onComplete(@NonNull com.google.android.gms.tasks.Task<AuthResult> task) {
                                        if (task.isSuccessful()) {
                                            User user = new User(name, email, password);

                                            userReference.child(FirebaseAuth.getInstance().getCurrentUser().getUid())
                                                    .setValue(user).addOnCompleteListener(new OnCompleteListener<Void>() {
                                                @Override
                                                public void onComplete(@NonNull com.google.android.gms.tasks.Task<Void> task) {
                                                    if (task.isSuccessful()) {
                                                        Toast.makeText(getApplicationContext(), "User registered successfully!", Toast.LENGTH_LONG).show();
                                                        startActivity(new Intent(LoginActivity.this, HomeActivity.class));
                                                        finish();
                                                    }
                                                }
                                            });

                                            taskReference.child(FirebaseAuth.getInstance().getCurrentUser().getUid())
                                                    .setValue("null").addOnCompleteListener(new OnCompleteListener<Void>() {
                                                @Override
                                                public void onComplete(@NonNull com.google.android.gms.tasks.Task<Void> task) {
                                                    if (task.isSuccessful()) {

                                                    }
                                                    else {

                                                    }
                                                }
                                            });
                                        }
                                    }
                                });


                        mAuth.signInWithEmailAndPassword(email, password).addOnCompleteListener(new OnCompleteListener<AuthResult>() {
                            @Override
                            public void onComplete(@NonNull com.google.android.gms.tasks.Task<AuthResult> task) {
                                if (task.isSuccessful()) {
                                    startActivity(new Intent(LoginActivity.this, HomeActivity.class));
                                    finish();
                                }
                                else {
                                    Toast.makeText(getApplicationContext(), "Invalid Email or Password!", Toast.LENGTH_LONG).show();
                                }
                            }
                        });
                    }
                });
                task.addOnFailureListener((e) -> {
                    startActivityForResult(service.getSignInIntent(), 1002);
                });
                progressBar.setVisibility(View.GONE);
            }
        });

        findViewById(R.id.login_register_button).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startActivity(new Intent(LoginActivity.this, RegisterActivity.class));
                finish();
            }
        });


    }

}