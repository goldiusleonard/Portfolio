package com.binus.ootd;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseUser;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;

import java.time.LocalDate;
import java.util.ArrayList;

public class ProfileActivity extends AppCompatActivity {
    private TextView name_text, num_task_text;

    private FirebaseDatabase rootNode;
    private DatabaseReference todayTaskReference, userReference;
    private FirebaseAuth mAuth;

    private String name;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_profile);

        name_text = findViewById(R.id.name_profile_text);
        num_task_text = findViewById(R.id.num_task_textview);

        LocalDate selectedDate = LocalDate.now();
        rootNode = FirebaseDatabase.getInstance();
        mAuth = FirebaseAuth.getInstance();

        todayTaskReference = rootNode.getReference("tasks").child(mAuth.getUid()).child(selectedDate.toString());
        userReference = rootNode.getReference("users").child(mAuth.getUid());

        ValueEventListener postListener = new ValueEventListener() {
            @Override
            public void onDataChange(DataSnapshot dataSnapshot) {
                Long count = dataSnapshot.getChildrenCount();
                num_task_text.setText(count.toString());
            }

            @Override
            public void onCancelled(DatabaseError databaseError) {

            }
        };
        todayTaskReference.addValueEventListener(postListener);

        userReference.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                User currentUser = snapshot.getValue(User.class);

                name = currentUser.getName();
                name_text.setText(name);
            }

            @Override
            public void onCancelled(@NonNull DatabaseError error) {

            }
        });
    }

    @Override
    public void onBackPressed() {
        super.onBackPressed();
        startActivity(new Intent(this, HomeActivity.class));
        finish();
    }

    public void logout(View view) {
        FirebaseAuth.getInstance().signOut();
        startActivity(new Intent(this, LoginActivity.class));
        finish();
    }

    public void back(View view) {
        startActivity(new Intent(this, HomeActivity.class));
        finish();
    }
}