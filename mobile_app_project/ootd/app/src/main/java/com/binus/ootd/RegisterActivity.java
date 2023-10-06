package com.binus.ootd;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.service.autofill.UserData;
import android.text.TextUtils;
import android.util.Patterns;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Toast;

import com.google.android.gms.tasks.OnCompleteListener;
import com.google.android.gms.tasks.Task;
import com.google.firebase.auth.AuthResult;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;

public class RegisterActivity extends AppCompatActivity {
    private EditText name_textbox, email_textbox, password_textbox, conf_password_textbox;
    private Button register_button;
    private FirebaseDatabase rootNode;
    private DatabaseReference userReference, taskReference;
    private FirebaseAuth mAuth;
    private ProgressBar progressBar;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_register);

        mAuth = FirebaseAuth.getInstance();
        rootNode = FirebaseDatabase.getInstance();
        userReference = rootNode.getReference("users");
        taskReference = rootNode.getReference("tasks");

        name_textbox = findViewById(R.id.register_name_textbox);
        email_textbox = findViewById(R.id.register_email_textbox);
        password_textbox = findViewById(R.id.register_password_textbox);
        conf_password_textbox = findViewById(R.id.register_conf_password_textbox);

        progressBar = findViewById(R.id.register_progressBar);

        register_button = findViewById(R.id.register_button);

        register_button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (validateInput()) {
                    if (validatePasswordConf()) {
                        String name = name_textbox.getText().toString().trim();
                        String email = email_textbox.getText().toString().trim();
                        String password = password_textbox.getText().toString().trim();

                        progressBar.setVisibility(View.VISIBLE);
                        mAuth.createUserWithEmailAndPassword(email, password)
                                .addOnCompleteListener(new OnCompleteListener<AuthResult>() {
                                    @Override
                                    public void onComplete(@NonNull Task<AuthResult> task) {
                                        if (task.isSuccessful()) {
                                            User user = new User(name, email, password);

                                            userReference.child(FirebaseAuth.getInstance().getCurrentUser().getUid())
                                                    .setValue(user).addOnCompleteListener(new OnCompleteListener<Void>() {
                                                @Override
                                                public void onComplete(@NonNull Task<Void> task) {
                                                    if (task.isSuccessful()) {
                                                        Toast.makeText(getApplicationContext(), "User registered successfully!", Toast.LENGTH_LONG).show();
                                                        progressBar.setVisibility(View.VISIBLE);
                                                        startActivity(new Intent(RegisterActivity.this, LoginActivity.class));
                                                        finish();
                                                    }
                                                    else {
                                                        Toast.makeText(getApplicationContext(), "Email has been registered!", Toast.LENGTH_LONG).show();
                                                        progressBar.setVisibility(View.GONE);
                                                    }
                                                }
                                            });

                                            taskReference.child(FirebaseAuth.getInstance().getCurrentUser().getUid())
                                                    .setValue("null").addOnCompleteListener(new OnCompleteListener<Void>() {
                                                @Override
                                                public void onComplete(@NonNull Task<Void> task) {
                                                    if (task.isSuccessful()) {

                                                    }
                                                    else {

                                                    }
                                                }
                                            });
                                        }
                                        else {
                                            Toast.makeText(getApplicationContext(), "Failed to register. Please Try Again!", Toast.LENGTH_LONG).show();
                                            progressBar.setVisibility(View.GONE);
                                        }
                                    }
                                });
                    }
                    else {
                        conf_password_textbox.setError("Confirmation Password not match!");
                        conf_password_textbox.requestFocus();
                    }
                }
                else {
                    if (conf_password_textbox.getText().toString().isEmpty()) {
                        conf_password_textbox.setError("Confirmation Password is required!");
                        conf_password_textbox.requestFocus();
                    }
                    if (password_textbox.getText().toString().isEmpty()) {
                        password_textbox.setError("Password is required!");
                        password_textbox.requestFocus();
                    }
                    if (password_textbox.getText().toString().trim().length() < 6) {
                        password_textbox.setError("Min password length should be 6 characters!");
                        password_textbox.requestFocus();
                    }
                    if (email_textbox.getText().toString().isEmpty()) {
                        email_textbox.setError("Email is required!");
                        email_textbox.requestFocus();
                    }
                    if (!Patterns.EMAIL_ADDRESS.matcher(email_textbox.getText().toString()).matches()) {
                        email_textbox.setError("Email is not valid!");
                        email_textbox.requestFocus();
                    }
                    if (name_textbox.getText().toString().isEmpty()) {
                        name_textbox.setError("Name is required!");
                        name_textbox.requestFocus();
                    }
                }
            }
        });

        findViewById(R.id.register_login_button).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                progressBar.setVisibility(View.VISIBLE);
                startActivity(new Intent(RegisterActivity.this, LoginActivity.class));
                finish();
                progressBar.setVisibility(View.GONE);
            }
        });

    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
        progressBar.setVisibility(View.VISIBLE);
        startActivity(new Intent(this, LoginActivity.class));
        finish();
        progressBar.setVisibility(View.GONE);
    }

    private boolean validateInput() {
        if (name_textbox.getText().toString().isEmpty() ||
                email_textbox.getText().toString().isEmpty() ||
                password_textbox.getText().toString().isEmpty() ||
                conf_password_textbox.getText().toString().isEmpty()) {
            return false;
        }
        if (!Patterns.EMAIL_ADDRESS.matcher(email_textbox.getText().toString()).matches()) {
            return false;
        }
        if (password_textbox.getText().toString().trim().length() < 6) {
            return false;
        }
        return true;
    }

    private boolean validatePasswordConf() {
        if (!password_textbox.getText().toString().equals(conf_password_textbox.getText().toString())) {
            return false;
        }
        return true;
    }
}